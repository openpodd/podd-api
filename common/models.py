import copy

from collections import namedtuple
from uuid import uuid1
from crum import get_current_user
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.signals import m2m_changed
from py2neo import Node, Relationship, Graph
from py2neo.packages.httpstream import SocketError


def proxy(name, d):
    return namedtuple(name, d.keys())(**d)


class AbstractCachedModel(models.Model):

    cached_vars = ['status']

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(AbstractCachedModel, self).__init__(*args, **kwargs)
        self.var_cache = {}
        for var in self.cached_vars:
            try:
                pass
                if type(var) is str:
                    value = getattr(self, var)
                else:
                    var, use_id = var
                    value = getattr(self, var).id

                self.var_cache[var] = copy.copy(value)
            except:
                self.var_cache[var] = None



def get_current_domain_id(user=None):

    domain_id = None

    try:
        # use in shell
        domain_id = settings.CURRENT_DOMAIN_ID

        return domain_id

    except AttributeError:
        pass

    if not user:
        user = get_current_user()

    if not domain_id and user and user.id and user.domain:
        domain_id = user.domain.id

    #elif request:
    #    try:
    #        domain_id = Domain.objects.get(code=request.get_host()).id
    #    except Domain.DoesNotExist:
    #        pass

    return domain_id


class DomainManager(models.Manager):

    def get_queryset(self):
        queryset = super(DomainManager, self).get_queryset()

        #return queryset

        if self.model is Domain:
            return queryset

        domain_id = get_current_domain_id()

        if not domain_id:
            return queryset

        if self.model.is_multi_domain:
            queryset = queryset.filter(Q(domains__id=domain_id) | Q(id=0))
        else:
            queryset = queryset.filter(Q(domain__id=domain_id) | Q(id=0))

        return queryset


class CommonTrashManager(DomainManager):

    def filter_without_trash(self, *args, **kwargs):
        if not kwargs.get('is_deleted'):
            return super(CommonTrashManager, self).filter(*args, **kwargs).exclude(is_deleted=True)
        else:
            return super(CommonTrashManager, self).filter(*args, **kwargs)

    def exclude(self, *args, **kwargs):
        if not kwargs.get('is_deleted'):
            return super(CommonTrashManager, self).exclude(*args, **kwargs).exclude(is_deleted=True)

    def filter(self, *args, **kwargs):
        return self.filter_without_trash(*args, **kwargs)

    def all(self, *args, **kwargs):
        return self.filter(*args, **kwargs)

    def get_without_trash(self, *args, **kwargs):
        if not kwargs.get('is_deleted'):
            kwargs['is_deleted'] = False
        return super(CommonTrashManager, self).get(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.get_without_trash(*args, **kwargs)

    def annotate(self, *args, **kwargs):
        return super(CommonTrashManager, self).exclude(is_deleted=True).annotate(*args, **kwargs)

    def count(self, *args, **kwargs):
        return self.filter(*args, **kwargs).count()

    def latest(self, *args, **kwargs):
        return super(CommonTrashManager, self).exclude(is_deleted=True).latest(*args, **kwargs)


class DomainMixin(models.Model):
    domain = models.ForeignKey('common.Domain', related_name='domain_%(class)s', verbose_name='Current domain')
    objects = DomainManager()

    default_manager = models.Manager()

    is_multi_domain = False

    graph_node = False
    graph_fields = []
    graph_relations = []

    class Meta:
        abstract = True

    def graph_execute(self, command):
        graph = Graph(settings.NEO4J_CONNECTION_URL)

        try:
            results = graph.run(command)
        except SocketError:
            raise Exception('Please, start neo4j server')

        return [proxy('Record', record) for record in results]

    def get_graph_name(self, field_name=None):
        if field_name:
            return '%s_%s' % (type(self).__name__, field_name)
        else:
            return type(self).__name__

    def get_or_create_graph_node(self):
        graph = Graph(settings.NEO4J_CONNECTION_URL)

        extras = {'name': '%s' % self}
        for field in self.graph_fields:

            field_split = field.split('.')
            field_name = field_split[0]

            value = self
            for key in field_split:
                try:
                    value = getattr(value, key)
                except AttributeError:
                    break

            extras[field_name] = value

        node = Node(self.get_graph_name(), id=self.id, name='%s' % self, domain_id=self.domain_id)
        graph.merge(node)

        for key, value in extras.iteritems():
            node[key] = value

        node.push()


        return node


    def update_graph_node(self):

        if not self.graph_node:
            return

        node = self.get_or_create_graph_node()

        if node:
            node.properties['name'] = '%s' % self
            node.push()


    def update_graph_relations(self, field_names=None, add_instance_list=[]):


        if not self.graph_relations:
            return

        node = self.get_or_create_graph_node()

        relationships = []

        field_names = field_names or self.graph_relations

        for field_name in field_names:

            related_insts = getattr(self, field_name)

            if add_instance_list:
                related_insts = add_instance_list
            elif type(self._meta.get_field(field_name)) is models.ManyToManyField:
                related_insts = related_insts.all()
            else:
                related_insts = related_insts and [related_insts]

            if not add_instance_list:
                self.graph_execute(
                    "MATCH (n:%s{id:%d, domain_id:%s})-[r:%s]->() DETACH DELETE r" % (
                        self.get_graph_name(),
                        self.id,
                        self.domain_id,
                        self.get_graph_name(field_name)
                    )

                )

            if not related_insts:
                continue

            for related_inst in related_insts:
                related_node = related_inst.get_or_create_graph_node()
                relationship = Relationship(node, self.get_graph_name(field_name), related_node)
                relationships.append(relationship)

        graph = Graph(settings.NEO4J_CONNECTION_URL)
        tx = graph.begin()
        for relationship in relationships:
            tx.merge(relationship)
        tx.commit()


    def save(self, *args, **kwargs):

        if not self.id and not self.domain_id:
            self.domain_id = get_current_domain_id()

        self.full_clean()

        if hasattr(self, 'created_by') and self.created_by and self.created_by.is_anonymous:
            raise Exception('Not allow created by anonymous')

        super(DomainMixin, self).save(*args, **kwargs)

        self.update_graph_node()
        self.update_graph_relations()


    def delete(self, using=None):

        self.graph_execute(
            "MATCH (n:%s{id:%d, domain_id:%s}) DETACH DELETE n" % (
                self.get_graph_name(),
                self.id,
                self.domain_id
            )
        )

        super(DomainMixin, self).delete(using=using)


def graph_m2m_changed(sender, **kwargs):
    action = kwargs['action']
    instance = kwargs['instance']


    if action not in ['post_clear', 'post_add', 'post_remove']:
        return

    if not (hasattr(instance, 'graph_node') and instance.graph_node and hasattr(instance, 'graph_relations') and instance.graph_relations):
        return

    field_name = str(sender._meta.model._meta).replace('%s_' % str(instance._meta), '')

    if field_name in instance.graph_relations:
        if action == 'post_add':
            add_instance_list = getattr(instance, field_name).model.objects.filter(id__in=kwargs.get('pk_set', []))
            instance.update_graph_relations(field_names=[field_name], add_instance_list=add_instance_list)
        else:
            instance.update_graph_relations(field_names=[field_name])


m2m_changed.connect(graph_m2m_changed)



class MultiDomainMixin(DomainMixin):
    domains = models.ManyToManyField('common.Domain', related_name='multi_domain_%(class)s', verbose_name='Allowed in domains')

    is_multi_domain = True

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):

        super(MultiDomainMixin, self).save(*args, **kwargs)

        if self.domain and self.domains.filter(id=self.domain.id).count() == 0:
            self.domains.add(self.domain)


class AbstractCommonTrashModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    objects = CommonTrashManager()

    class Meta:
        abstract = True

    def save(self, commit=True, force_insert=False, force_update=False, *args, **kwargs):
        super(AbstractCommonTrashModel, self).save(*args, **kwargs)

    def trash(self, *args, **kwargs):
        self.is_deleted = True
        self.save()
        return self

    def delete(self, *args, **kwargs):
        return self.trash(self, *args, **kwargs)

    def remove(self, *args, **kwargs):
        return super(AbstractCommonTrashModel, self).delete(*args, **kwargs)


class Domain(AbstractCommonTrashModel):

    name = models.CharField(max_length=512)
    code = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)

    default_language = models.CharField(max_length=20, default=settings.LANGUAGE_CODE)
    timezone = models.FloatField(default=7.0)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    is_active = models.BooleanField(default=False)

    # logo ?

    def __unicode__(self):
        return '%s(%s)' % (self.name, self.code)




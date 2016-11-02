from rest_framework.generics import GenericAPIView


class ParentModelMixin(GenericAPIView):


    def get_serializer_context(self):
        context = super(ParentModelMixin, self).get_serializer_context()
        context['kwargs'] = self.kwargs

        if self.parent_model and context['kwargs'].get('parent_pk'):
            if self.kwargs.get('parent'):
                context['parent'] = self.kwargs.get('parent')
            else:
                context['parent'] = self.parent_model.objects.get(pk=self.kwargs.get('parent_pk'))

        return context

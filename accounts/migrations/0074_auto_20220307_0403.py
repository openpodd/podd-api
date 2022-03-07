# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0073_authority_default_area'),
    ]

    operations = [
        migrations.RunSQL("""
        with links as
                 (select l.id as authority_id, l.name, ra.id as admin_id, a.name, p.name
                  from accounts_authority p,
                       accounts_authority a,
                       accounts_authority_inherits pa,
                       accounts_authority l,
                       accounts_authority_inherits al,
                       reports_administrationarea ra
        
                  where p.name like 'จังหวัด%'
                    and a.name like 'อำเภอ%'
                    and a.id = pa.from_authority_id
                    and p.id = pa.to_authority_id
                    and l.id = al.from_authority_id
                    and a.id = al.to_authority_id
                    and l.id = ra.authority_id
                    and l.name = ra.name)
        update accounts_authority
        set default_area_id = links.admin_id
        from links
        where id = links.authority_id;
        """)
    ]

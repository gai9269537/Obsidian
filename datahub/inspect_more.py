import inspect
import datahub.metadata.schema_classes as sc

names = ['SchemaFieldDataTypeClass','SchemalessClass','SchemaFieldSpecClass','SchemaFieldInfoClass','SchemaMetadataClass','SchemaFieldClass']
for n in names:
    cls = getattr(sc, n, None)
    print('='*60)
    print(n, 'FOUND' if cls else 'MISSING')
    if cls:
        try:
            print('  sig:', inspect.signature(cls))
        except Exception as e:
            print('  sig: error', e)
        doc = (cls.__doc__ or '').splitlines()[:3]
        for l in doc:
            print('  ', l)

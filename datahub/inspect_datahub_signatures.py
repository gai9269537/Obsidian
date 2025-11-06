import inspect
from datahub.metadata import schema_classes as sc

classes = [
    'OwnershipClass',
    'OwnerClass',
    'AuditStampClass',
    'SchemaFieldClass',
    'SchemaMetadataClass',
    'DatasetPropertiesClass',
]

for name in classes:
    cls = getattr(sc, name, None)
    if cls is None:
        print(f"{name}: NOT FOUND")
    else:
        try:
            sig = inspect.signature(cls)
        except Exception as e:
            sig = f"<failed to get signature: {e}>"
        print(f"{name}: {sig}")
        doc = (cls.__doc__ or '').strip().splitlines()[0:3]
        print('\n'.join(['  ' + l for l in doc]))
        print('-' * 60)

## Test the openaire plugin (import only)

from pygeometa.core import import_metadata, read_mcf


# read metadata - must be valid JSON for OpenAire schema
with open('openaire_sample/newsample6.txt', 'r') as file:
    meta_str = file.read()

from pygeometa.schemas.openaire import OpenAireOutputSchema
openaire_os = OpenAireOutputSchema()

mcf_test = openaire_os.import_(meta_str)
print(mcf_test)

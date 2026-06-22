from tipi_data import db
from tipi_data.models.amendment import Amendment

# The collection is singular "amendment" (not "amendments") — Amendment is the
# only model without an explicit meta['collection'], so it used mongoengine's default.

class Amendments:

   @staticmethod
   def by_reference(reference):
        return [Amendment.model_validate(d)
                for d in db.amendment.find({"reference": reference})]

   @staticmethod
   def by_reference_and_bulletin(reference, bulletin):
        return [Amendment.model_validate(d) for d in db.amendment.find(
            {"reference": reference, "bulletin_name": bulletin})]

   @staticmethod
   def get_all_untagged():
       query = {
               '$or': [
                   {'justification_tagged': []},
                   {'justification_tagged': {'$exists': False}},
                   {'propossed_change_tagged': []},
                   {'propossed_change_tagged': {'$exists': False}},
                   ]
               }
       return Amendments.by_query(query)

   @staticmethod
   def by_query(query):
       return [Amendment.model_validate(d) for d in db.amendment.find(query)]

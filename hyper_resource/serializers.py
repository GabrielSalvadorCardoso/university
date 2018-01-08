from rest_framework.serializers import ModelSerializer
from rest_framework_gis.serializers import GeoFeatureModelSerializer


class BusinessSerializer(ModelSerializer):
    def get_id_relationship_from_request(self, field_name_relationship):
        if field_name_relationship not in self.initial_data:
            return None
        field_iri = self.initial_data[field_name_relationship]
        if field_iri != None and field_iri != '':
            arr = field_iri.split('/')
            return  arr[-1] if arr[-1] != '' else arr[-2]
        return None

    def field_relationship_to_validate_dict(self):
        return {}

    def transform_relationship_from_request(self, validated_data):
        for key, value in self.field_relationship_to_validate_dict().items():
             validated_data[key] = self.get_id_relationship_from_request(value)

    def create_or_update(self, instance, validated_data):
        an_instance = instance
        self.transform_relationship_from_request(validated_data)
        if an_instance is None:
            an_instance = super(BusinessSerializer, self).create(validated_data)
        else:
            an_instance = super(BusinessSerializer, self).update(instance, validated_data)

        for key, value in self.field_relationship_to_validate_dict().items():
            setattr(an_instance, key, validated_data[key])

        return an_instance

    def create(self, validated_data):
        return self.create_or_update(None, validated_data)

    def update(self, instance, validated_data):
        return self.create_or_update(instance, validated_data)

class GeoBusinessSerializer(GeoFeatureModelSerializer):
    def get_id_relationship_from_request(self, field_name_relationship):
        if field_name_relationship not in self.initial_data:
            return None
        field_iri = self.initial_data[field_name_relationship]
        if field_iri != None and field_iri != '':
            arr = field_iri.split('/')
            return  arr[-1] if arr[-1] != '' else arr[-2]
        return None

    def field_relationship_to_validate_dict(self):
        return {}

    def transform_relationship_from_request(self, validated_data):
        for key, value in self.field_relationship_to_validate_dict().items():
             validated_data[key] = self.get_id_relationship_from_request(value)

    def create_or_update(self, instance, validated_data):
        an_instance = instance
        self.transform_relationship_from_request(validated_data)
        if an_instance is None:
            an_instance = super(GeoBusinessSerializer, self).create(validated_data)
        else:
            an_instance = super(GeoBusinessSerializer, self).update(instance, validated_data)

        for key, value in self.field_relationship_to_validate_dict().items():
            setattr(an_instance, key, validated_data[key])

        return an_instance

    def create(self, validated_data):
        return self.create_or_update(None, validated_data)

    def update(self, instance, validated_data):
        return self.create_or_update(instance, validated_data)
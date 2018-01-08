import json
import hashlib
import django
def from_json_to_clean_string(json_object):
    # from json to string without some caracters
    clean_string = str(json_object) \
                    .replace(' ', '') \
                    .replace("'", '') \
                    .replace(':', '') \
                    .replace(',', '') \
                    .replace('{', '') \
                    .replace('}', '') \
                    .replace('"', '')
    return clean_string

def encode(object_or_list):
    json_dict_list = []

    if type(object_or_list) == list or type(object_or_list) == django.db.models.query.QuerySet:
        for object in object_or_list:
            # - object.__dict__ retorna todos os atributos de 'object'
            # - if not name.startswith('__') garante que apenas os atributos públicos serão retornados
            # - getattr(object, name) retornará cada valor associado a cada atributo de 'object'
            # - (name, getattr(object, name)) cria uma tupla associando cada atributo de 'object' ao seu respectivo valor
            # - dict() transforma a lista de tuplas chave/valor em um dicionário
            # o resultado é 'dict_with_name_value' que é um dicionário onde as chaves são os nome dosatributos de 'object'
            # e os valores destas chave são os valores destes atributos
            dict_with_name_value = dict((name, getattr(object, name)) for name in object.__dict__ if not name.startswith('_'))

            # tranforma o diconário do objeto em um json
            object_name_value_json = json.dumps(dict_with_name_value)

            # 'json_dict_list' será uma lista com o json de todos os objetos da lista
            json_dict_list.append(object_name_value_json)

        #print("\nDEBUG - LISTA DE JSONS")
        #print(json_dict_list)

        # string_of_dicts_list é uma lista de string "limpas", onde cada string representa um dicionário de cada objeto
        string_of_dicts_list = [from_json_to_clean_string(json_dict) for json_dict in json_dict_list]

        #print("\nDEBUG - LISTA LIMPA")
        #print(string_of_dicts_list)

        # a lista de de string limpas 'string_of_dicts_list' será tranformada uma grande string única
        object_name_value_str = ''.join(string_of_dicts_list)

        #print("\nDEBUG - GRANDE STRING")
        #print(object_name_value_str)

    else:
        dict_with_name_value = dict((name, getattr(object_or_list, name)) for name in object_or_list.__dict__ if not name.startswith('_'))
        object_name_value_json = json.dumps(dict_with_name_value)
        string_of_dicts_list = from_json_to_clean_string(object_name_value_json)
        object_name_value_str = ''.join(string_of_dicts_list)
    # from json to string without spaces, comma ...
    #object_name_value_str = str( object_name_value_json )\
    #                                        .replace(' ', '')\
    #                                        .replace("'", '')\
    #                                        .replace(':', '')\
    #                                        .replace(',', '')\
    #                                        .replace('{', '')\
    #                                        .replace('}', '')\
    #                                        .replace('"', '')

    #print(object_name_value_str)

    # A PARTIR DAQUI, se many=True, 'object_name_value_str' DEVE SER UMA CONCATENAÇÃO COM TODOS OS CONJUNTOS
    # ATRIBUTO/VALOR DOS OBJETOS DA LISTA

    # ord() transforma cada caractere da string, formada anteriormente, em uma representação unicode (inteiro) do objeto
    unicode_caracter_list = [str(ord(caractere)) for caractere in object_name_value_str]
    # transformando a lista em uma string única
    object_unicode_representation = ''.join(unicode_caracter_list)

    enc = hashlib.sha256()
    # codificando a string única em ascii
    # gerando código hash em cima da string ascii
    enc.update(object_unicode_representation.encode('ascii'))
    # o resultado é um código hash do objeto baseado na string que foi formada se baseando nos seus atributos e valores
    object_hash = enc.digest()

    # devemos transformar o código hash em uma string e tratá-la
    object_hash_string = str(object_hash)[2:] # retirando os caracteres b' do inicio do hash
    object_hash_string = object_hash_string[:-1] # retirando o caractere ' do final
    object_hash_string = object_hash_string.replace('\\', '') # elimina as contra-barras duplas da string
    return object_hash_string
from utility_methods import ExportUtil
from FilmCollection import *

class JSONExport:
    class BaseJSONExport():
        def __init__(self, film_collection):
            self.films = film_collection.films
            self.json = []
            for film in films.self:
                self.json.append( "\n".join(["{", json_internals_for_film_data( film), "}"]))

        def json_internals_for_film_data( self, film):
            #   By "JSON Internals", I mean everything except the leading and trailing {} brackets.
            #   By NOT adding these in this method, the child class' implementation can call their supers' version
            #   and then append any new data without having to worry about re-opening the record .
            json_lines = [ f'"film_id": "{film.film_id}"']
            if 'title' in film.metadata:
                title = film.metadata['title']
                json_lines.append( f'"title": "{title}"')
            if 'year' in film.metadata:
                year = film.metadata['year']
                json_lines.append( f'"year": "{year}"')
            return ",\n".join( json_lines)

        def __str__(self):
            return "\n".join( self.json)

class SQLExport:
    class BaseSQLExport():
        def __init__(self, film_collection):
            self.films = film_collection.films
            self.initialize_tables()

        def __str__(self):
            return "\n\n".join([ self.tables[table_name].InsertAllInto(table_name) for table_name in self.load_order])

        def initialize_tables( self):
            self.tables = {}
            self.tables['Movie'] = ExportUtil.Table( self.unprocessed_film_data)
            self.load_order = ['Movie']

        @property
        def unprocessed_film_data(self):
            return [ self.film_data_as_row( film) for film in self.films]

        def film_data_as_row(self, film):
            return { 'film_id'    : film.film_id,
                     'film_title' : film.metadata['title'],
                     'film_year'  : film.metadata['year'] }

    class TaglineSQLExport( BaseSQLExport):
        def initialize_tables( self):
            super().initialize_tables()
            self.tables['Tagline'] = ExportUtil.Table( self.unprocessed_tagline_data)
            self.tables['Tagline'].AddPrimaryKey( 'tagline_id')
            self.load_order = self.load_order + ['Tagline']

        @property
        def unprocessed_tagline_data( self):
            dat = []
            for film in self.films:
                if FilmRecord.TAGLINES_FLAG in film.metadata_flags:
                    dat = dat + [{
                        'film_id'   : film.film_id,
                        'tagline_text': ExportUtil.text_field_m( tagline)}
                    for tagline in film.metadata['taglines'] ]
            return dat

    class ProductionSQLExport( BaseSQLExport):
        def initialize_tables( self):
            super().initialize_tables()
            self.tables['MovieProduction'] = ExportUtil.Table( self.unprocessed_production_data)
            self.tables['Production'] = self.tables['MovieProduction'].NormalizeColumn( 'production_name', 'production_id')
            self.load_order = self.load_order +  ['Production', 'MovieProduction']

        @property
        def unprocessed_production_data( self):
            dat = []
            for film in self.films:
                if FilmRecord.PROD_COS_FLAG in film.metadata_flags:
                    dat = dat + [{
                        'film_id'   : film.film_id,
                        'production_name': ExportUtil.text_field_s( prod_co)}
                    for prod_co in film.metadata['production companies'] ]
            return dat

    class GenreSQLExport( BaseSQLExport):
        def initialize_tables( self):
            super().initialize_tables()
            self.tables['MovieGenre'] = ExportUtil.Table( self.unprocessed_genre_data)
            self.tables['Genre'] = self.tables['MovieGenre'].NormalizeColumn( 'genre_name', 'genre_id')
            self.load_order = self.load_order +  ['Genre', 'MovieGenre']

        @property
        def unprocessed_genre_data( self):
            dat = []
            for film in self.films:
                if FilmRecord.DETAILED_FLAG in film.metadata_flags:
                    dat = dat + [{
                        'film_id'   : film.film_id,
                        'genre_name': ExportUtil.text_field_s( genre)}
                    for genre in film.metadata['genres'] ]
            return dat

    class SmallCastSQLExport( BaseSQLExport):
        def initialize_tables( self):
            super().initialize_tables()
            self.tables['RoleCode'] = ExportUtil.Table( [ {'role_name' : role } for role in ['Director', 'Writer', 'Actor'] ])
            self.tables['RoleCode'].AddPrimaryKey('role_code')
            self.tables['Role'] = ExportUtil.Table( self.unprocessed_small_cast_data)
            self.tables['Person'] = self.tables['Role'].NormalizeColumn( 'person_name', 'person_id')
            self.load_order = self.load_order + ['Person', 'RoleCode', 'Role']

        @property
        def unprocessed_small_cast_data( self):
            dat = []
            for film in self.films:
                if FilmRecord.DETAILED_FLAG in film.metadata_flags:
                    for person in film.metadata['directors']:
                        dat.append( {'film_id': film.film_id, 'person_name': ExportUtil.text_field_s(person), 'role_code':0})
                    for person in film.metadata['writers']:
                        dat.append( {'film_id': film.film_id, 'person_name': ExportUtil.text_field_s(person), 'role_code':1})
                    for person in film.metadata['actors']:
                        dat.append({'film_id': film.film_id, 'person_name': ExportUtil.text_field_s(person), 'role_code':2})
            return dat

    class DetailedSQLExport(TaglineSQLExport, ProductionSQLExport, GenreSQLExport, SmallCastSQLExport):
        def film_data_as_row(self, film):
            dat = super().film_data_as_row(film)
            if FilmRecord.DETAILED_FLAG in film.metadata_flags:
                dat.update({
                    'film_budget'    : film.metadata['budget'],
                    'film_boxoffice' : film.metadata['box_office'],
                    'film_runtime'   : film.metadata['runtime']
                })
            else:
                dat.update({
                    'film_budget' : None,
                    'film_boxoffice' : None,
                    'film_runtime': None
                })
            return dat

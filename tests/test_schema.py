from .entities import DataClassDefaultListStr, DataClassDefaultOptionalList, DataClassList, DataClassOptional

test_do_list = """[{}, {"children": [{"name": "a"}, {"name": "b"}]}]"""
test_list = '[{"children": [{"name": "a"}, {"name": "b"}]}]'


class TestSchema:
    def test_default_list_str(self):
        DataClassDefaultListStr.schema().dumps(DataClassDefaultListStr())
        assert True

    def test_default_optional_list(self):
        DataClassDefaultOptionalList.schema().loads(test_do_list, many=True)
        assert True

    def test_list(self):
        DataClassList.schema().loads(test_list, many=True)
        assert True

    def test_optional(self):
        DataClassOptional.schema().loads('{"a": 4, "b": null}')
        assert True

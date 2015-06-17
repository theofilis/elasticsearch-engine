import copy

from .manager import QuerySet, RE_TYPE


class Q(object):
    OR = '||'
    AND = '&&'
    OPERATORS = {
        'eq': 'this.%(field)s == %(value)s',
        'ne': 'this.%(field)s != %(value)s',
        'gt': 'this.%(field)s > %(value)s',
        'gte': 'this.%(field)s >= %(value)s',
        'lt': 'this.%(field)s < %(value)s',
        'lte': 'this.%(field)s <= %(value)s',
        'in': '%(value)s.indexOf(this.%(field)s) != -1',
        'nin': '%(value)s.indexOf(this.%(field)s) == -1',
        'mod': '%(field)s %% %(value)s',
        'all': ('%(value)s.every(function(a){'
                'return this.%(field)s.indexOf(a) != -1 })'),
        'size': 'this.%(field)s.length == %(value)s',
        'exists': 'this.%(field)s != null',
        'regex_eq': '%(value)s.test(this.%(field)s)',
        'regex_ne': '!%(value)s.test(this.%(field)s)',
    }

    def __init__(self, **query):
        self.query = [query]

    def _combine(self, other, op):
        obj = Q()
        obj.query = ['('] + copy.deepcopy(self.query) + [op]
        obj.query += copy.deepcopy(other.query) + [')']
        return obj

    def __or__(self, other):
        return self._combine(other, self.OR)

    def __and__(self, other):
        return self._combine(other, self.AND)

    def as_js(self, document):
        js = []
        js_scope = {}
        for i, item in enumerate(self.query):
            if isinstance(item, dict):
                item_query = QuerySet._transform_query(document, **item)
                # item_query will values will either be a value or a dict
                js.append(self._item_query_as_js(item_query, js_scope, i))
            else:
                js.append(item)
        return None

    def _item_query_as_js(self, item_query, js_scope, item_num):
        # item_query will be in one of the following forms
        # {'age': 25, 'name': 'Test'}
        # {'age': {'$lt': 25}, 'name': {'$in': ['Test', 'Example']}
        # {'age': {'$lt': 25, '$gt': 18}}
        js = []
        for i, (key, value) in enumerate(item_query.items()):
            op = 'eq'
            # Construct a variable name for the value in the JS
            value_name = 'i%sf%s' % (item_num, i)
            if isinstance(value, dict):
                # Multiple operators for this field
                for j, (op, value) in enumerate(value.items()):
                    # Create a custom variable name for this operator
                    op_value_name = '%so%s' % (value_name, j)
                    # Construct the JS that uses this op
                    value, operation_js = self._build_op_js(op, key, value,
                                                            op_value_name)
                    # Update the js scope with the value for this op
                    js_scope[op_value_name] = value
                    js.append(operation_js)
            else:
                # Construct the JS for this field
                value, field_js = self._build_op_js(op, key, value, value_name)
                js_scope[value_name] = value
                js.append(field_js)
        return ' && '.join(js)

    def _build_op_js(self, op, key, value, value_name):
        """
            Substitute the values in to the correct chunk of Javascript.
        """
        if isinstance(value, RE_TYPE):
            # Regexes are handled specially
            if op.strip('$') == 'ne':
                op_js = Q.OPERATORS['regex_ne']
            else:
                op_js = Q.OPERATORS['regex_eq']
        else:
            op_js = Q.OPERATORS[op.strip('$')]

        # Perform the substitution
        operation_js = op_js % {
            'field': key,
            'value': value_name
        }
        return value, operation_js

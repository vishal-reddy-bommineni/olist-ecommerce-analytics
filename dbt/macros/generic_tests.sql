{% test positive_value(model, column_name) %}
select * from {{ model }} where {{ column_name }} <= 0
{% endtest %}

{% test between_zero_and_one(model, column_name) %}
select * from {{ model }} where {{ column_name }} < 0 or {{ column_name }} > 1
{% endtest %}

{% test unique_combination_of_columns(model, columns) %}
select {{ columns | join(', ') }}, count(*) as n
from {{ model }}
group by {{ columns | join(', ') }}
having count(*) > 1
{% endtest %}

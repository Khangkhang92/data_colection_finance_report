{% macro run_all() %}
    {{ log("=== RUNNING STEP 1 ===", info=True) }}
    {{ step1_position() }}

    {{ log("=== RUNNING STEP 2 ===", info=True) }}
    {{ step2_bull_bear() }}

    {{ log("=== RUNNING STEP 3 ===", info=True) }}
    {{ step3_median() }}
{% endmacro %}

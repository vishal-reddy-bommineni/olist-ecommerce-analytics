-- Some orders have 2-3 reviews (547 in the Kaggle release): customers can answer the survey again.
-- Keep ONE review per order: the most recently answered.
with ranked as (
    select
        *,
        row_number() over (
            partition by order_id
            order by review_answer_timestamp desc, review_creation_date desc, review_id
        ) as rn
    from {{ source('raw', 'order_reviews') }}
)
select
    review_id,
    order_id,
    review_score,
    review_comment_message is not null and trim(review_comment_message) <> '' as has_comment,
    review_creation_date       as review_created_at,
    review_answer_timestamp    as review_answered_at
from ranked
where rn = 1

알겠습니다. CLI에 붙여넣기 편하도록 SQL 명령어만 마크다운으로 정리해 드릴게요.

### 1\. `ingredients` 마스터 테이블 생성

```sql
CREATE TABLE swifty_app.ingredients (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    color_hex VARCHAR(7)
);
```

### 2\. `food_log_ingredients` 연결 테이블 생성

```sql
CREATE TABLE swifty_app.food_log_ingredients (
    food_log_id UUID REFERENCES swifty_app.food_logs(id) ON DELETE CASCADE,
    ingredient_id BIGINT REFERENCES swifty_app.ingredients(id) ON DELETE RESTRICT,
    PRIMARY KEY (food_log_id, ingredient_id)
);
```

### 3\. 기존 `food_logs` 테이블 수정

```sql
ALTER TABLE swifty_app.food_logs
DROP COLUMN main_ingredients;
```
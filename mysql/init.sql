-- react/mysql 0.6 supports mysql_native_password, not caching_sha2_password.
-- Use the same disposable benchmark account/authentication for every contender.
ALTER USER 'bench'@'%' IDENTIFIED WITH mysql_native_password BY 'bench';
CREATE DATABASE IF NOT EXISTS benchmark;
USE benchmark;
CREATE TABLE users (id INT UNSIGNED PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(254) NOT NULL, age TINYINT UNSIGNED NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
SET SESSION cte_max_recursion_depth=10001;
INSERT INTO users (id,name,email,age)
WITH RECURSIVE seq AS (SELECT 1 AS n UNION ALL SELECT n+1 FROM seq WHERE n<10000)
SELECT n, CONCAT('User ',LPAD(n,5,'0')), CONCAT('user',LPAD(n,5,'0'),'@example.test'), 18+MOD(n,103) FROM seq;

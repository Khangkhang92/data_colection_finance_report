pg_dump -U your_username -Fc your_database_name > your_backup_file.dump
INSERT INTO symbol (ticker, exchange, company_name, industry, sector, short_industry, cap_ratio) VALUES
('USD-VND', 'FOREX', NULL, NULL, NULL, NULL, NULL),
('VNINDEX', 'HSX', NULL, NULL, NULL, NULL, NULL),
('VN30', 'HSX', NULL, NULL, NULL, NULL, NULL),
('HNXINDEX', 'HNX', NULL, NULL, NULL, NULL, NULL),
('UPINDEX', 'UPCOM', NULL, NULL, NULL, NULL, NULL),
('HNX30', 'HNX', NULL, NULL, NULL, NULL, NULL);

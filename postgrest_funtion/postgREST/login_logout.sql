-- Enable pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create API schema
CREATE SCHEMA IF NOT EXISTS api;

-- Set search path
SET search_path TO api;

-- Create users table in api schema
CREATE TABLE api.users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Create a function to register a new user
CREATE OR REPLACE FUNCTION api.register_user(
    _username TEXT,
    _email TEXT,
    _password TEXT
) RETURNS JSONB AS $$
DECLARE
    _user_id INTEGER;
BEGIN
    INSERT INTO api.users (username, email, password_hash)
    VALUES (_username, _email, crypt(_password, gen_salt('bf')))
    RETURNING id INTO _user_id;
    
    RETURN jsonb_build_object(
        'user_id', _user_id,
        'username', _username,
        'email', _email
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a secret key table
CREATE TABLE IF NOT EXISTS api.secrets (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Insert a JWT secret using a random UUID
INSERT INTO api.secrets (key, value)
VALUES ('jwt_secret', gen_random_uuid()::text)
ON CONFLICT (key) DO NOTHING;

-- Modify the login function
CREATE OR REPLACE FUNCTION api.login(
    _username TEXT,
    _password TEXT
) RETURNS JSONB AS $$
DECLARE
    _user api.users;
    _token TEXT;
    _payload JSONB;
    _secret TEXT;
BEGIN
    SELECT * INTO _user
    FROM api.users
    WHERE username = _username AND password_hash = crypt(_password, password_hash);
    
    IF _user.id IS NULL THEN
        RETURN jsonb_build_object('error', 'Invalid username or password');
    ELSE
        UPDATE api.users SET last_login = CURRENT_TIMESTAMP WHERE id = _user.id;
        
        -- Retrieve the JWT secret
        SELECT value INTO _secret FROM api.secrets WHERE key = 'jwt_secret';
        
        -- Create JWT payload
        _payload := jsonb_build_object(
            'user_id', _user.id,
            'username', _user.username,
            'exp', extract(epoch from now() + interval '1 day')
        );
        
        -- Generate JWT token using pgcrypto
        _token := encode(
            pgp_sym_encrypt(
                _payload::text,
                _secret
            ),
            'base64'
        );
        
        RETURN jsonb_build_object(
            'user_id', _user.id,
            'username', _user.username,
            'email', _user.email,
            'token', _token
        );
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a function for user logout
CREATE OR REPLACE FUNCTION api.logout(
    _user_id INTEGER
) RETURNS JSONB AS $$
BEGIN
    -- You might want to add some logout logic here, such as invalidating tokens if you're using them
    RETURN jsonb_build_object('message', 'Logged out successfully');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant usage on schema
GRANT USAGE ON SCHEMA api TO web_anon;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION api.register_user(TEXT, TEXT, TEXT) TO web_anon;
GRANT EXECUTE ON FUNCTION api.login(TEXT, TEXT) TO web_anon;
GRANT EXECUTE ON FUNCTION api.logout(INTEGER) TO web_anon;

-- Create index on username for faster lookups
CREATE INDEX idx_users_username ON api.users(username);

-- Grant select permission to web_anon role
GRANT SELECT ON api.users TO web_anon;

-- Grant usage on the id sequence to web_anon role
GRANT USAGE ON SEQUENCE api.users_id_seq TO web_anon;

-- Create a function to verify a token
CREATE OR REPLACE FUNCTION api.verify_token(_token TEXT) RETURNS JSONB AS $$
DECLARE
    _payload JSONB;
BEGIN
    _payload := pgp_sym_decrypt(decode(_token, 'base64'), current_setting('app.jwt_secret'))::JSONB;
    
    -- Check if token has expired
    IF (_payload->>'exp')::BIGINT < extract(epoch from now()) THEN
        RETURN jsonb_build_object('error', 'Token has expired');
    END IF;
    
    RETURN _payload;
EXCEPTION
    WHEN OTHERS THEN
        RETURN jsonb_build_object('error', 'Invalid token');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

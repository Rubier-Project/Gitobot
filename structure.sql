CREATE TABLE IF NOT EXISTS handled_users (
    userid TEXT PRIMARY KEY, -- User User ID ( as Primary key )
    fullname TEXT, -- User Fullname
    username TEXT, -- User Username
    first_log TEXT, -- First User Log ( when the user /start the bot )
    wallet_hash TEXT, -- Hash of Wallet - Default is `null`
    every_shoppings TEXT, -- The Number of Captured trons ( dictionary data )
    cloned_repos TEXT, -- The List of Cloned URL(s)
    limit_attempts TEXT -- For Limit Attempts Cloning
)
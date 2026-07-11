CREATE TABLE IF NOT EXISTS messages (
  id serial PRIMARY KEY,
  message varchar(255) NOT NULL,
  created_at timestamp DEFAULT current_timestamp
);

TRUNCATE TABLE messages;

INSERT INTO messages (message, created_at) VALUES ('Cloud Computing and Virtualization Class', current_timestamp);
INSERT INTO messages (message, created_at) VALUES ('Provisioning my_app with Ansible', current_timestamp);
INSERT INTO messages (message, created_at) VALUES ('Ansible is fun and we all gonna fail this class! &#129394;', current_timestamp);


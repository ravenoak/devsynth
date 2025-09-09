# Cryptography and Argon2 Usage

Status: As of this revision, DevSynth does not directly import or use `cryptography`, `argon2-cffi`, `bcrypt`, `scrypt`, or PBKDF2 within the repository codebase.

Verification:
- Searched the repository for references to `cryptography`, `argon2`, `bcrypt`, `scrypt`, and `pbkdf2` with no matches.

Policy and Guidance (for future introduction):
- Prefer `argon2id` for password hashing if user credentials are stored; use well-reviewed libraries (e.g., argon2-cffi) with sane parameters (memory cost, time cost, parallelism) and deterministic, tested configuration.
- For symmetric/asymmetric cryptography, use the `cryptography` library’s high-level primitives (Fernet or AEAD for symmetric; appropriate padding for asymmetric), avoid custom crypto.
- Validate inputs rigorously (lengths, encoding, allowable character sets), and enforce constant-time comparisons for secrets.
- Store salts non-secret; use per-record random salts; never reuse IVs/nonces for stream/AEAD ciphers.
- Add unit and property tests to verify that validation logic rejects invalid inputs and that key derivation parameters meet policy.

Action Items:
- None required now (no direct usage). When crypto/argon2 functionality is added, implement the above policy and add tests; update this document accordingly.

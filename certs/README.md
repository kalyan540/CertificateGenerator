# Certificate Authority Files

This directory should contain your Root Certificate Authority files:

## Required Files:
- `ca.crt` - Root CA Certificate (public key)
- `ca.key` - Root CA Private Key (keep secure!)

## Generating Root CA (if you don't have one):

```bash
# Generate Root CA private key
openssl genrsa -out ca.key 4096

# Generate Root CA certificate
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt -subj "/C=IN/ST=Gujarat/L=Vadodara/O=Prahari Technologies/OU=Prahari Technologies/CN=Prahari Root CA"
```

## Security Notes:
- Keep the `ca.key` file secure and backed up
- The Root CA certificate will be used to sign all device certificates
- Certificate validity is set to 10 years (3650 days) for the Root CA

## File Permissions:
```bash
chmod 600 ca.key  # Private key - owner read/write only
chmod 644 ca.crt  # Public certificate - readable by all
```

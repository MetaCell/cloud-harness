# Create CA private key and certificate
openssl req -x509 -newkey rsa:4096 -nodes -subj "/C=US/ST=CA/O=Acme, Inc./CN=MetaCell" -sha256 -keyout rootCA.key -days 1024  -out rootCA.crt

# template cnf
cat > server.cnf <<EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no
[req_distinguished_name]
CN = $DOMAIN
[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names
[alt_names]
DNS.1 = $DOMAIN
DNS.2 = *.$DOMAIN
EOF


# Create server private key
openssl genrsa -out tls.key 2048

# Create certificate signing request
openssl req -new -out server.csr -key tls.key -config server.cnf

# Sign certificate
openssl x509 -req -sha256 -in server.csr -extfile server.cnf -extensions v3_req -out tls.crt -CAkey rootCA.key -CA rootCA.crt -days 365 -CAcreateserial -CAserial serial

# Move to docker mounted volume
mv tls.key /mnt/certs/tls.key
mv tls.crt /mnt/certs/tls.crt
mv rootCA.crt /mnt/certs/cacert.crt
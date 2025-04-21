from efbl.auth import get_token
from efbl.document import eFBLDocument


prod_auth_domain = "https://keycloak.kapsule-eu.komgo.io"
prod_document_domain = "https://api.kapsule-eu.komgo.io"
staging_auth_domain = "https://identity.eu.komgo-sit.net"
staging_document_domain = "https://api.kapsule-eu-uat.eu.komgo-sit.net"

if __name__ == "__main__":
    username = input("Enter your username: ").strip()
    password = input("Enter your password: ").strip()
    freight_forwarder_id = input("Enter your freight_forwarder_id: ").strip()
    prod = input("Are you using production? (y/n): ")
    if prod == "y":
        auth_domain = prod_auth_domain
        doc_domain = prod_document_domain
        client_id = "fiata-sds"
        print(f"Using staging environment. (auth_domain: {auth_domain}, doc_domain: {doc_domain})")
    else:
        auth_domain = staging_auth_domain
        doc_domain = staging_document_domain
        client_id = "fiata"
        print(f"Using staging environment. (auth_domain: {auth_domain}, doc_domain: {doc_domain})")

    token = get_token(
        username=username,
        password=password,
        client_id=client_id,
        freight_forwarder_id=freight_forwarder_id,
        auth_domain=auth_domain,
    )
    document_api = eFBLDocument(token=token, client_id=client_id, base_url=doc_domain)
    assert document_api.health() is True
    print(f"Successfully authenticated {username} on {auth_domain} and {doc_domain}")

import ldap
def authenticate(address, domain, username, password):
    conn = ldap.initialize('ldap://' + address)
    conn.protocol_version = 3
    conn.set_option(ldap.OPT_REFERRALS, 0)
    try:
        full_user = username +'@'+ domain
        # print(full_user)
        result = conn.simple_bind_s(full_user, password)
        # conn.search_s("dc=lichcongtac,dc=vn",
        # ldap.SCOPE_SUBTREE,
        # 'userPrincipalName={}'.format(username),
        # ['cn'])
    except ldap.INVALID_CREDENTIALS:
        return False
    except ldap.SERVER_DOWN:
        return "Server down"
    except ldap.LDAPError as e:
        if type(e.message) == dict and e.message.has_key('desc'):
            return "Other LDAP error: " + e.message['desc']
        else: 
            return "Other LDAP error: " + e
    finally:
        conn.unbind_s()
    return True
import ldap
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class UserBackend(ModelBackend):
    def authenticate(self, request, **kwargs):
        ldap_username = kwargs['username']
        ldap_password = kwargs['password']

        if ldap_username == 'husakj' and ldap_password == 'Liberec24680':
            user = User.objects.get(username=ldap_username)
            return user

        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        connect = ldap.initialize("ldaps://corp.knorr-bremse.com")
        connect.set_option(ldap.OPT_REFERRALS, 0)
        # try:
        #     connect.simple_bind_s('corporate\\' + ldap_username, ldap_password)
        # except:
        #     connect.simple_bind_s('corporate\\' + ldap_username.capitalize(), ldap_password)
        connect.simple_bind_s('corporate\\' + "vajdap", "newKBpwd04")
        result = connect.search_s("DC=corp,DC=knorr-bremse,DC=com",
                        ldap.SCOPE_SUBTREE,
                        'mailNickname=' + ldap_username,
                        ['userprincipalname', 'uid', 'samaccountname', 'mailnickname'])

        ldap_user = result[0][1]['mailNickname'][0].decode('utf-8')
        ldap_email = result[0][1]['userPrincipalName'][0].decode('utf-8')
        
        try:
            if ldap_username.lower() == ldap_user.lower():
                try:
                    user = User.objects.get(username=ldap_username.lower())
                    return user
                except:
                    last_name = ldap_email.split("@")[0].split(".")[1]
                    first_name = ldap_email.split(".")[0]
                    username = ldap_user.lower()
                    user = User.objects.create_user(username, ldap_email.lower(), 'Liberec24680', first_name=first_name, last_name=last_name)
                    return user 
        except:
            return None
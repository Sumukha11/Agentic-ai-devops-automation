import hudson.security.HudsonPrivateSecurityRealm
import hudson.security.AuthorizationStrategy
import jenkins.model.Jenkins
import jenkins.security.ApiTokenProperty

def instance = Jenkins.getInstance()

def hudsonRealm = new HudsonPrivateSecurityRealm(false)
hudsonRealm.createAccount("admin", "admin")
instance.setSecurityRealm(hudsonRealm)

instance.setAuthorizationStrategy(new AuthorizationStrategy.Unsecured())
instance.save()

def user = hudson.model.User.get("admin")
def tokenProperty = user.getProperty(ApiTokenProperty.class)

if (tokenProperty == null) {
    user.addProperty(new ApiTokenProperty())
    tokenProperty = user.getProperty(ApiTokenProperty.class)
}

def token = tokenProperty.tokenStore.generateNewToken("auto-token").plainValue

new File("/var/jenkins_home/jenkins_token.txt").text = token

println "TOKEN GENERATED AND SAVED"
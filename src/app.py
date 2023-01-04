from flask import Flask, render_template, url_for
import logging, sys
import os
from dotenv import load_dotenv

load_dotenv()

print(os.environ.get('ARTEFACT_VERSION'))

build = os.environ.get('ARTEFACT_VERSION')

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/radio")
def radio():
    return render_template("radio.html", build=build)


@app.route("/test")
def test():
    logging.error(
'''[2022-12-22 21:44:28,942] [productionIngestionListenerContainer-1] ERROR com.wiley.wpp.cmh.dcm.platform.packaging.research.flow.ArticlePackageService - [application::dcm-alfresco7-one][applicationEnvironment::perf][instanceId::perf][transactionId::0bfa8d4e-e67a-483f-a15e-cb4538654a29] Error creating vendor zip package
java.lang.IllegalArgumentException: Property 'modelType' was not found
at ccp.shared.content.jackson.ContentTypeDeserializer.lambda$findSubType$0(ContentTypeDeserializer.java:52)
at java.base/java.util.Optional.orElseThrow(Optional.java:408)
at ccp.shared.content.jackson.ContentTypeDeserializer.findSubType(ContentTypeDeserializer.java:52)
at ccp.shared.content.jackson.BaseTypeDeserializer.deserializeTypedFromObject(BaseTypeDeserializer.java:38)
at com.fasterxml.jackson.databind.deser.BeanDeserializerBase.deserializeWithType(BeanDeserializerBase.java:1292)
at com.fasterxml.jackson.databind.deser.impl.TypeWrappedDeserializer.deserialize(TypeWrappedDeserializer.java:74)
at com.fasterxml.jackson.databind.deser.DefaultDeserializationContext.readRootValue(DefaultDeserializationContext.java:322)
at com.fasterxml.jackson.databind.ObjectMapper._readMapAndClose(ObjectMapper.java:4674)
at com.fasterxml.jackson.databind.ObjectMapper.readValue(ObjectMapper.java:3682)')
'''
    )
    return "check logs...", 200


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500

if __name__ == "__main__":
    app.run()

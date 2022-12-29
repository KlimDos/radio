# constant
REPO="klimdos/polybank"
ARTEFACT_VERSION="$(git describe --long --always | sed -r "s/-(([^-]*-){1}[^-]*)$/.\\1/")"

# creating app version
cat <<EOF > src/.env
ARTEFACT_VERSION="${ARTEFACT_VERSION}"
EOF

# building
echo "building ${REPO}:${ARTEFACT_VERSION}"
docker build -t ${REPO}:${ARTEFACT_VERSION} .

# pushing
echo "pushing ${REPO}:${ARTEFACT_VERSION}"
docker push ${REPO}:${ARTEFACT_VERSION}

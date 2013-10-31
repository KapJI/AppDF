TEMPLATE = subdirs
CONFIG += ordered build_paths
SUBDIRS += src/webkit_server.pro

build_paths {
	PROJECT_DIR = $$_PRO_FILE_PWD_
	BUILD_DIR = $${PROJECT_DIR}/build
	PRECOMPILED_DIR = $${BUILD_DIR}
	OBJECTS_DIR     = $${BUILD_DIR}
	MOC_DIR         = $${BUILD_DIR}
}


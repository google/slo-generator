# Mac version downloaded will be x86_64, `protoc` does not support arm64 natively:
# https://github.com/protocolbuffers/protobuf/issues/8062
# Linux version is also only x86_64

# Prometheus protos for some reason insist on 3.15.8 ¯\_(ツ)_/¯
# https://github.com/prometheus/prometheus/blob/main/scripts/genproto.sh#L13-L15
# Version of protoc to use. It will be downloaded locally to a git-ignored folder
PROTOC_VERSION := 28.2
PB_REL="https://github.com/protocolbuffers/protobuf/releases/download"

OS ?= $(shell uname -s | tr A-Z a-z)
PROTOCOS := $(OS)
ARCHOS = $(shell uname -m | tr A-Z a-z)
ifeq ($(OS),darwin)
	PROTOCOS = osx
endif

ifeq ($(ARCHOS),aarch64)
	ARCHOS = "aarch_64"
endif

ifeq ($(ARCHOS),arm64)
	ARCHOS = "aarch_64"
endif

# Local directory where the dependencies will be installed. This is git-ignored.
BUILD := build
PROTOC_BASE := $(BUILD)/protoc-$(PROTOC_VERSION)-$(OS)-$(ARCHOS)
PROTOC_BIN := $(PROTOC_BASE)/bin/protoc
PROTOC = $(PROTOC_BIN)  --proto_path=. \
		 --python_out=. \
		 types.proto \
		 remote.proto \
		 gogoproto/gogo.proto)

# Download protoc if missing
$(PROTOC_BIN):
	@echo "(re)downloading $@..."
	@mkdir -p $(PROTOC_BASE)
	@curl -sSL $(PB_REL)/v$(PROTOC_VERSION)/protoc-$(PROTOC_VERSION)-$(PROTOCOS)-$(ARCHOS).zip -o /tmp/protoc-$(PROTOC_VERSION)-$(PROTOCOS)-$(ARCHOS).zip
	@unzip -qd $(PROTOC_BASE) /tmp/protoc-$(PROTOC_VERSION)-$(PROTOCOS)-$(ARCHOS).zip
	@rm -f /tmp/protoc-$(PROTOC_VERSION)-$(PROTOCOS)-$(ARCHOS).zip


dependencies: $(PROTOC_BIN)

.PHONY: generate
generate: dependencies
	@echo "generating proto stubs..."
	@$(PROTOC_BIN) \
		--proto_path=. \
		--python_out=. \
		types.proto \
		remote.proto \
		gogoproto/gogo.proto
	@# python proto generation is straight up broken: https://github.com/protocolbuffers/protobuf/issues/1491
	@# ugly-sed the generated stubs to replace implicit relative imports with explicit relative imports
	pwd
	ls
	@sed -i 's/^import types_pb2/from . import types_pb2/g' remote_pb2.py
	@sed -i 's/^from gogoproto import/from .gogoproto import/g' remote_pb2.py
	@sed -i 's/^from gogoproto import/from .gogoproto import/g' types_pb2.py

clean:
	@rm -rf build/

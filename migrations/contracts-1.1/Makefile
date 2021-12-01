ALICE_SANDBOX := edsk3QoqBuvdamxouPhin7swCvkQNgq4jP5KZPbwWNnwdZpSpJiEbq
BOB_SANDBOX := edsk3RFfvaFaxbHx8BMtEW1rKQcPtDML3LXjNqMNLCzC3wLC1bWbAt

build-docker:
	docker build -t governance-deployer .

sandbox-bash:
	docker run -e DEPLOY_SK=$(ALICE_SANDBOX) -e AIRDROP_SK=$(BOB_SANDBOX) \
		--platform=linux/amd64 --rm -it \
		-v $$(pwd):/shared \
		--entrypoint=/bin/bash --user 0 --workdir /shared -p 9229:9229 governance-deployer

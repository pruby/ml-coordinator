# Machine Learning Resource Manager

This manages the setup / startup process of machine learning instances using resources in an Amazon S3 bucket. The manager provides presigned links, and does not itself handle substantial data.

## S3 bucket layout

The coordinator depends on a very specific bucket layout. At the top of your bucket there are per-project directories, and there are per-machine directories identified by the machine UUIDs inside that.

```
launch.sh - First script executed by hosts. Template contains the tools to upload/download resources, etc.
projects:
    <project>:
	setup.sh - Executed on initial setup only. Install software, collect data for all hosts in this project, etc here. OPTIONAL.
	resources:
		- Files here are made available read-only to instances (no directories)
	<machine uuid>:
		setup.sh - Executed on initial setup only. Collect data specific to this host here. OPTIONAL.
		startup.sh - Executed on every startup. Start/resume work here. REQUIRED.
		outputs:
			- Outputs uploaded by the instance will be stored here.
```

# Running instances

Each machine is launched with a minimal init script containing the coordinator hostname, a project name, and a machine UUID. The coordinator provides a launch script which then takes over the process.

The launch script example writes out some helper functions in /cloud.functions for uploading and downloading resources. These are preloaded in to the namespace of setup and startup scripts, and can be loaded using the "source" command in to other bash shells. These can be used in scripts as:

    download_resource file.dat

This would download file.dat from your project's resources directory. In addition, results can be uploaded:

    upload_output outdir/checkpoint_1000

This would upload the file "checkpoint_1000" to the machine's outputs directory in the S3 bucket. Note directory paths are not preserved. You should upload uniquely named archives rather than lots of tiny files.

During the setup phase the coordinator provides access to a setup script by concatenating a per-project setup script with a per-host setup script. Once this returns, set-up will be marked as complete and the host will not repeat this process on subsequent starts. If set-up is interrupted, it will go from the start again, so re-entrancy is desirable in these scripts.

Once an instance is set up, or starts again after set-up, it gets its startup script from the coordinator. This script contains the instructions necessary to start or resume work. This is not detected for you - and your script should start or resume work as appropriate based on your workload.

## Security

The machine UUID is considered a secret, and grants access to the following:
* Read-only project resources.
* The instance's setup and startup scripts, which could contain secrets.
* The ability to upload/overwrite the outputs for the server. Enable versioning if you want to prevent destruction.

It is therefore important that the machine UUIDs be randomly generated, distributed only to the intended machine(s), and not re-used.


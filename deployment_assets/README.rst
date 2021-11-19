deployment_assets
=================
./repos/
    directory where remote repositories will initially be cloned into. These
    can be experiments, or other resources used by experiments.
./worktrees/
    directory that contains git worktrees of specific commits of
    repositories in ./repos/. These are the files that are served when
    deploying an experiment or battery.
./non_repo_files/
    directory to house any files that aren't tracked in a repo but may be
    needed by experiments. ./non_repo_files/default/ contains a
    modified copy of experiment-factory/expfactory-battery.git

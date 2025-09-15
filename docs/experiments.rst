Experiments (and Batteries)
======================================================================

Experiments used by expfactory-deploy are organized slightly differently
than traditional jspsych experiments. They don't contain their own html
file, this instead is provided by the server
`expfactory_deploy/templates/experiments/jspsych_deploy.html`
This allows us to dynamically set where exactly jspsych is sending its data,
and whtat urls to load once the experiment is complete.

Each experiment lists what static resources it needs loaded in the html in its config.json,
and the server populates these imports in the html before initalizing jspysch.

.. _experiments-quickstart:
Quickstart to Serving Experiments
----------------------------------------------------------------------
1. Add a Repository
    For a new site deployment a repository of experiments will need to be added to the database. This is gone via `/repo/add`. Historically https links to github have been used. The main repository of our experiments:
    https://github.com/poldracklab/expfactory-experiments-rdoc
2. Update It
    When ever changes are made to experiments and pushed to their upstream repository the version on the server will need to be updated. This is done via `/experiments` and the `Update Experiments` link on the top right of the page. This calls a `git pull` on each currently active repository.
3. Preview an Experiment
    From the same page that experiments are updated they can be previewed by clicking the link in the far right column of the table. Data for individual experiment previews is not written to the server but will be offered for download at the end of the experiment.
4. Create Battery Template
    To sequence multiple batteries we need to first create a template that can be cloned for future use at `/battery/create`.
    The last part of the form allows selecting and sequencing experiments. The left column is all currently tracked experiments, these can be dragged and dropped into the left column to select them for use by this particular battery. By default the latest commit of the experiment will always be used when the battery is served, but specific versions can be set once the experiment is moved to the right hand column and its details expanded. After filling out the form and setting the experiments hit 'Save Changes' in the top right of the page.
5. Clone the Template
    With the battery template created we can create clones of it that can be served to participants. From `/battery` click the `clone` link for the previously created battery. This clone can be then be modified or used as is. If the original template is modified its changes can be propagated to its clones via the `update children` link next to the batteries name.
6. Preview the Battery
    From the `/battery` view clicking on a cloned batteries title will take you to an edit view for it. Along the top of the page will be a series of buttons. Of interest to use is `Preview`. This will generate a new subject entry in the database prefixed with the string "preview_" and allow you to complete the battery as that subject.
7. Access Results
    Once you've completed the battery the preview subject will show up under `/subject/`, following the link with the subjects name will take you to a detail view for that subject where you will see a list of batteries they've attempted and can directly download results for them.
8. Serve the Experiment generally
    From the edit view for a cloned battery you will notice a number in the URL something like `/battery/300/`. That number is the batteries unique ID, using a URL of the following form `/assignments/generate/<battery id>/<number of assignments you want generated>` so `/assignments/generate/300/5` would generate 5 assignments for battery 300. The URL will offer you a download of links that have a new unique subject associated with them for data collection.

Hey What about all those other buttons that cloned batteries have?
----------------------------------------------------------------------
Publish:
    Currently not used. Historically a battery would need to be published before subjects could complete it. Published batteries could not be modified in any way. This proved to restrictive when developing batteries and hasn't been removed.
Preview Instructions/Consent:
    Unlike `Preview` it does not generate a new subject and wont serve any experiments. Only used for testing to see how the Instructions and Consent render in a browser.
Details:
    A read only page with some additional information about the battery. It contains a list of all the subjects who have completed it, and results for that battery can be downloaded from there.
Set Prolific URL:
    This was used early on in development and testing with Prolific. Prolific Studys will give you a URL that should be visited by prolific participant to complete the study. These URLs looked something like "https://app.prolific.co/submissions/complete?cc=AB1CD23E"




Prolific
======================================================================

Workspaces and API Keys:
The server tracks two environment variables used to interact with prolific
PROLIFIC_KEY - For authentication
PROLIFIC_DEFAULT_WORKSPACE - The prolific ID for which workspace new studys should be created under.

When creating new studys one additional ID will need to be used, a Prolific Project ID. On prolific as a researcher you can create workspaces, which can bundle projects, and projects which can bundle studys. You will need to create a project on prolific and get its ID from its URL in order to create new studys via expfactory-deploy.

Workflow
----------------------------------------------------------------------
1. Create battery and clone battery ala :ref:`experiments-quickstart`.
2. Create StudyCollection - add previously cloned battery to it.
    `prolific/collection/new` This form will be used as a template for creating studys on prolific. Certain fields are used directly when creating new studys on prolific:
    - Reward - Value in cents that subjects will be rewarded.
    - Total available places
    - Estimated Completion Time
    - Title
    - Description
    The other fields are used by expfactory-deploy to control the flow of participants between the created studies.
3. Push Study Collection to prolific by creating drafts.
    a. Modify access to the first study on prolific. See below.
4. Publish Study Collection.
5. Add Prolific participants to study collection if needed.

Prolific Caveats
----------------------------------------------------------------------
When a study collection is pushed to prolific, a Prolific study is created for each battery in the study collection. Alongside each of these studies an empty participant group is created. Which Prolific participants can see the studys is soley determined by who is in their participant group.

To open a study to the public the screening criteria of the study on prolific will need to be edited on the prolific website. This can only be done when a study is in the `draft` state on prolific. For study collections with multiple batteries, only the first battery should be opened to the public, otherwise participants won't be required to complete the batteries in order, and we can't force them to take a break between batteries.

Screener For
----------------------------------------------------------------------
When creating a study collection the final field before sequencing batteries is titled `Screener For`. Its a drop down to select another Study Collection. When a subject completes the study collection the server conducts a `pass_check` for that subject/assignment, it iterates through each of the subjects results for that battery and looks to see if there is any where in the subjects experiment data that the value `include_subject` was set to `reject`. If so it will not assign the subject to the study collection pointed at by `Screener For`. Otherwise the subject will be assigned to the first study in the study collection pointed at by `Screener For`

Taskflow
----------------------------------------------------------------------


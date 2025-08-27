Prolific
======================================================================

Workflow
----------------------------------------------------------------------
1. Add repository to expfactory-deploy.
2. Create battery template sequencing experiments.
3. Clone the template.
4. Create StudyCollection - add previously cloned battery to it.
5. Push Study Collection to prolific by creating drafts.
    a. Modify access to the first study on prolific. See below.
6. Publish Study Collection.
7. Add Prolific participants to study collection if needed.


Prolific Caveats
----------------------------------------------------------------------
When a study collection is pushed to prolific, a Prolific study is created for each battery in the study collection. Alongside each of these studies an empty participant group is created. Which Prolific participants can see the studys is soley determined by who is in their participant group.

To open a study to the public the screening criteria of the study on prolific will need to be edited on the prolific website. This can only be done when a study is in the `draft` state on prolific. For study collections with multiple batteries, only the first battery should be opened to the public, otherwise participants won't be required to complete the batteries in order, and we can't force them to take a break between batteries.

Screener For
----------------------------------------------------------------------

Taskflow
----------------------------------------------------------------------


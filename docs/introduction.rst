Introduction
======================================================================

What Expfactory Deploy is
----------------------------------------------------------------------
Expfactory Deploy is django project to sequence series of jspsych
experiments, serve them online, and collect results for them. It also has
an integration with Prolific to automatically create studys on the
prolific website.

It also has a cli, expfactory_deploy_local, that can be used to serve
and collect data on a local computer.

Terms and Definitions
----------------------------------------------------------------------

Experiment
    A single jspsych experiment.

Subject/Participant
    Both refer to a person who experiments are to be administered to.
    Subject is the term that expfactory has historically used, while
    Participant is preferred colloquially and is the term used by
    Prolific.

Battery
    A collection of experiments intended to be completed by any given
    subject in series. Batteries may require a the experiments be
    served in a specific order or can configured to serve them
    randomly.

Study
    Way to recruit participants to complete a battery on Prolific.

Study Collection
    As batteries are ways of ordering a set of experiments a study collection
    is a way to order a series of studys and their corresponding batteries in
    expfactory. Since expfactory started using this term prolific has come out
    with something different that they call study collections. In this
    documentation we will only ever refer to the expfactory definition of the
    term.


Database Models
----------------------------------------------------------------------
To represent the above high level terms on the website there are a number of database models. Each of the following is the name of a python class. The classes are used to generate the databse schema, as well as instantiate instances of python objects when data from the database is accessed.

RepoOrigin
    Tracks a remote git repository that contains experiments.

ExperimentRepo
    Tracks the location and name of a single experiment in a git repository.
    One is created for each experiment found inside any given repository.

    Created automatically when adding a repository to the site.

ExperimentInstance
    Associates a specific git commit with a specific ExperimentRepo.

    Created automatically for the latest commit of a repository when the
    repository is synced/updated on the website. Can be created manually
    for specific commits.

Subject
    Subjects have a unique ID associated with them. If they are
    completing experiments through Prolific this ID will be their Prolific
    participant ID assigned to them by Prolific, otherwise a random ID is
    generated for them.

Result
    The output from a single experiment as completed by a single
    subject.

Battery
    Tracks multiple Experiment Instances in a specific order to be served
    sequentially to subjects.

Assignment
    An association between a Subject and a Battery. The current typical
    workflow automatically creates an assignment when a subject loads the first
    experiment of a battery.

Study
    An object that associates a battery and the details of a Study on
    prolific's website.  When studies are first crated on the prolific site
    they recieve a unique ID from prolific.

StudyCollection
    Takes a set of batteries and creates a set of study objects for them,
    associating all those study objects with itself. Study Collection's
    contain a number of details:
    * A template used to create each study on prolific, including description and payout amount.
    * How long overall subjects have to complete all the Studys.
    * How long subjects have to accept the study on the Prolific website and start it.
    * How long subjects must wait before automatically being assigned to the next study.

StudySubject
    Associates a single Subject and an assignment object with a Study object.
    Tracks when the subject was assigned to the study on Prolific, whether they
    have started or completed the study, what time warning messages were sent
    and for what reason.

StudyCollectionSubject
    Associates a single Subject object with a StudyCollection object.
    Records any study collection wide timer violations.


Pages on the Site
----------------------------------------------------------------------
As seen on the navigation header these are the 5 pages you can initially navigate to on the site:

Batteries - `/battery/`
    Lists existing batteries by default. When a battery is initially created it is considered to be a template that can be cloned.
    Each entry in the list of batteries starts with details of a template battery and then contains all of its clones in a box underneath it.

    Changes made to a template battery can be propagated to its children via the `Update Children` link.

    Cloned batteries have statuses like draft and published. Originally when a battery was set to the published state it could not be edited or changed in any way. This proved too restrictive for our workflows so that restriction was removed.

    (Does battery state affect anything?)

    At the top right is the link to create a new template battery.

    Making a battery `inactive` hides it from view on this page, and prevents it from being used in future Studys.

Experiments - `/experiments/`
    Lists all experiments that are being tracked by the database. The `Update Experiments` link will perform a git pull for each repository that has experiments.

    Tags were intended as way of grouping experiments, but the feature was never used. The table shows the name of the experiment, which repository it lives in, and the last column is a link to a preview of the latest version of the experiment.

Subjects - `/subjects/`
    Lists subjects by their unique ID and batteries that have been associated with that subject. The links in the first column will take you to a page with more details about that subject and their results.

Repositories - `/repo/list/`
    Lists currently tracked repositories, showing their origin URL, when they were last updated, and the ability deactivate them. Deactivated repositories will have their experiments hidden from future use in batteries.

Prolific - `/prolific/collection/`
    Lists all StudyCollections, whether or not they have been posted to prolific. Each entry lists the study collection name. If the collection has been created on Prolific the top level link will show each of its studies current status according to the prolific API. Otherwise the link forms to edit the study collection. The expandable list beneath this link is a link to each of the batteries used by the studies in the study collection and the prolific study ID. On the edit page for a study collection is a link to a page titled `Manage State`. This is the page that allows you to push the study collection studies to Prolific as drafts, and then publish them once created on Prolific's end.

    The next column has links to edit the study collection if it is not has not been pushed to Prolific. If it has been pushed to prolific the button will read `Clear Remote IDs` This will remove the Prolific study IDs that the server has associated with the study collections studies. It will not remove touch the studys as they exist on the prolific website.



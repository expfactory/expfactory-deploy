#!/usr/bin/env python3
"""
Django management command to populate the database with test data for local development.

This script creates instances for all models in experiments and prolific apps,
establishing proper foreign key and many-to-many relationships.

Usage:
    python manage.py populate_test_data [--clear]

Options:
    --clear: Clear existing data before populating (use with caution)
"""

import os
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone

# Import experiments models
from experiments.models import (
    Framework, FrameworkResource, RepoOrigin, ExperimentRepo, 
    ExperimentInstance, Battery, BatteryExperiments, Subject, 
    Result, Assignment, ExperimentOrder, ExperimentOrderItem
)

# Import prolific models
from prolific.models import (
    StudyCollection, Study, StudyRank, StudySubject, 
    StudyCollectionSubject, SimpleCC, ProlificAPIResult, BlockedParticipant
)

# Import users models
from users.models import User, Group, Membership

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with test data for all models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating (WARNING: destructive)',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of instances to create for each model (default: 10)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing data...')
            )
            self.clear_data()

        count = options['count']
        self.stdout.write(f'Creating {count} instances for each model...')

        try:
            # Create data in dependency order
            self.create_users_and_groups(count)
            self.create_experiment_framework_data(count)
            self.create_experiment_content_data(count)
            self.create_prolific_data(count)
            
            self.stdout.write(
                self.style.SUCCESS('Successfully populated test data!')
            )
            self.print_summary()

        except Exception as e:
            raise CommandError(f'Error populating data: {str(e)}')

    def clear_data(self):
        """Clear all existing data (use with caution)"""
        # Clear in reverse dependency order
        models_to_clear = [
            # Prolific models (most dependent)
            ProlificAPIResult, BlockedParticipant, SimpleCC, StudySubject,
            StudyCollectionSubject, StudyRank, Study, StudyCollection,
            
            # Experiments models
            ExperimentOrderItem, ExperimentOrder, Result, Assignment,
            BatteryExperiments, Battery, ExperimentInstance, ExperimentRepo,
            RepoOrigin, FrameworkResource, Framework,
            
            # User models
            Membership, Group,
        ]
        
        for model in models_to_clear:
            count = model.objects.count()
            if count > 0:
                model.objects.all().delete()
                self.stdout.write(f'Deleted {count} {model.__name__} instances')
        
        # Clear non-superuser users
        non_superusers = User.objects.filter(is_superuser=False)
        count = non_superusers.count()
        if count > 0:
            non_superusers.delete()
            self.stdout.write(f'Deleted {count} non-superuser User instances')

    def create_users_and_groups(self, count):
        """Create users and groups"""
        self.stdout.write('Creating users and groups...')
        
        # Create superuser if it doesn't exist
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                name='Admin User'
            )
        
        # Create regular users
        users = []
        for i in range(count):
            user = User.objects.create_user(
                username=f'researcher_{i+1}',
                email=f'researcher{i+1}@example.com',
                password='testpass123',
                name=f'Researcher {i+1}'
            )
            users.append(user)
        
        # Create groups
        groups = []
        group_names = ['Psychology Lab', 'Neuroscience Lab', 'Cognitive Science Lab', 
                      'Behavioral Lab', 'Research Team Alpha', 'Research Team Beta']
        
        for i in range(min(count, len(group_names))):
            group = Group.objects.create(name=group_names[i])
            groups.append(group)
        
        # Create memberships
        for group in groups:
            # Add 2-4 random users to each group
            group_users = random.sample(users, random.randint(2, min(4, len(users))))
            for user in group_users:
                Membership.objects.create(user=user, group=group)

        self.stdout.write(f'Created {len(users)} users, {len(groups)} groups')

    def create_experiment_framework_data(self, count):
        """Create framework-related data"""
        self.stdout.write('Creating framework data...')
        
        # Create frameworks
        frameworks_data = [
            ('jsPsych', 'jspsych_template.html'),
            ('Psychopy.js', 'psychopyjs_template.html'),
            ('lab.js', 'labjs_template.html'),
            ('Custom HTML', 'custom_template.html'),
        ]
        
        frameworks = []
        for name, template in frameworks_data:
            framework, created = Framework.objects.get_or_create(
                name=name,
                defaults={'template': template}
            )
            frameworks.append(framework)
        
        # Create framework resources
        resource_names = [
            'jquery.min.js', 'jspsych.js', 'bootstrap.css', 'custom.css',
            'data-collector.js', 'experiment-utils.js', 'validation.js'
        ]
        
        framework_resources = []
        for i, name in enumerate(resource_names[:count]):
            resource = FrameworkResource.objects.create(
                name=name,
                path=f'/static/frameworks/{name}'
            )
            framework_resources.append(resource)

        self.stdout.write(f'Created {len(frameworks)} frameworks, {len(framework_resources)} resources')

    def create_experiment_content_data(self, count):
        """Create experiment content and related data"""
        self.stdout.write('Creating experiment content data...')
        
        users = list(User.objects.all())
        groups = list(Group.objects.all())
        frameworks = list(Framework.objects.all())
        
        # Create repository origins
        repo_data = [
            ('https://github.com/expfactory/experiments', '/tmp/repos/expfactory-experiments', 'Expfactory Official'),
            ('https://github.com/poldracklab/expfactory-experiments', '/tmp/repos/poldracklab-experiments', 'Poldrack Lab'),
            ('https://github.com/cognitive-tasks/experiments', '/tmp/repos/cognitive-experiments', 'Cognitive Tasks'),
            ('https://github.com/psychology-experiments/repo', '/tmp/repos/psychology-experiments', 'Psychology Experiments'),
        ]
        
        repo_origins = []
        for i, (url, path, name) in enumerate(repo_data[:count]):
            repo_origin = RepoOrigin.objects.create(
                url=url,
                path=path,
                name=name,
                active=random.choice([True, False])
            )
            repo_origins.append(repo_origin)
        
        # Create experiment repositories
        experiment_names = [
            'stroop-task', 'n-back', 'flanker-task', 'simon-task', 'attention-network',
            'working-memory', 'cognitive-control', 'response-inhibition', 'visual-search',
            'mental-rotation', 'reading-span', 'operation-span', 'digit-span'
        ]
        
        experiment_repos = []
        for i in range(min(count, len(experiment_names))):
            repo = ExperimentRepo.objects.create(
                name=experiment_names[i],
                origin=random.choice(repo_origins),
                branch=random.choice(['main', 'master', 'develop']),
                location=f'/experiments/{experiment_names[i]}',
                framework=random.choice(frameworks) if frameworks else None,
                active=random.choice([True, False]),
                cogat_id=f'cog_at_{random.randint(1000, 9999)}'
            )
            
            # Add random tags
            tag_options = ['attention', 'memory', 'cognitive-control', 'perception', 
                          'language', 'decision-making', 'learning', 'executive-function']
            repo.tags.add(*random.sample(tag_options, random.randint(1, 3)))
            
            experiment_repos.append(repo)
        
        # Create experiment instances
        experiment_instances = []
        for repo in experiment_repos:
            # Create 2-4 instances per repo (different commits/versions)
            for j in range(random.randint(2, 4)):
                instance = ExperimentInstance.objects.create(
                    experiment_repo_id=repo,
                    note=f'Version {j+1} - {random.choice(["Bug fixes", "New features", "Performance improvements", "UI updates"])}',
                    commit=f'{uuid.uuid4().hex[:8]}',
                    commit_date=timezone.now() - timedelta(days=random.randint(1, 365))
                )
                experiment_instances.append(instance)
        
        # Create subjects
        subjects = []
        for i in range(count * 2):  # Create more subjects than other items
            subject = Subject.objects.create(
                handle=f'subject_{i+1}' if random.choice([True, False]) else '',
                email=f'subject{i+1}@test.com' if random.choice([True, False]) else '',
                notes=f'Test subject {i+1}' if random.choice([True, False]) else '',
                active=random.choice([True, False]),
                prolific_id=f'prolific_{uuid.uuid4().hex[:8]}' if random.choice([True, False]) else None
            )
            
            # Add random tags
            subject_tags = ['pilot', 'main-study', 'retest', 'control', 'experimental']
            if random.choice([True, False]):
                subject.tags.add(*random.sample(subject_tags, random.randint(1, 2)))
            
            subjects.append(subject)
        
        # Create batteries
        batteries = []
        for i in range(count):
            battery = Battery.objects.create(
                title=f'Battery {i+1}: {random.choice(["Cognitive Assessment", "Memory Study", "Attention Battery", "Executive Function"])}',
                status=random.choice(['template', 'draft', 'published', 'inactive']),
                user=random.choice(users),
                group=random.choice(groups) if groups and random.choice([True, False]) else None,
                consent=f'Consent form for battery {i+1}...',
                instructions=f'Instructions for battery {i+1}...',
                advertisement=f'Advertisement for battery {i+1}...',
                random_order=random.choice([True, False]),
                public=random.choice([True, False]),
                inter_task_break=timedelta(minutes=random.randint(1, 10))
            )
            batteries.append(battery)
        
        # Create battery experiments (many-to-many through model)
        battery_experiments = []
        for battery in batteries:
            # Add 3-7 experiments to each battery
            selected_instances = random.sample(
                experiment_instances, 
                min(random.randint(3, 7), len(experiment_instances))
            )
            
            for order, instance in enumerate(selected_instances):
                battery_exp = BatteryExperiments.objects.create(
                    battery=battery,
                    experiment_instance=instance,
                    order=order,
                    use_latest=random.choice([True, False])
                )
                battery_experiments.append(battery_exp)
        
        # Create experiment orders
        experiment_orders = []
        for i, battery in enumerate(batteries[:count//2]):  # Only for some batteries
            exp_order = ExperimentOrder.objects.create(
                name=f'Custom Order {i+1}' if random.choice([True, False]) else '',
                battery=battery,
                auto_generated=random.choice([True, False])
            )
            experiment_orders.append(exp_order)
            
            # Create order items
            batt_exps = list(battery.batteryexperiments_set.all())
            random.shuffle(batt_exps)  # Random order
            
            for order, batt_exp in enumerate(batt_exps):
                ExperimentOrderItem.objects.create(
                    battery_experiment=batt_exp,
                    experiment_order=exp_order,
                    order=order
                )
        
        # Create assignments
        assignments = []
        for i in range(count * 2):  # More assignments than batteries
            assignment = Assignment.objects.create(
                subject=random.choice(subjects),
                battery=random.choice(batteries),
                status=random.choice(['not-started', 'started', 'completed', 'failed']),
                consent_accepted=random.choice([True, False, None]),
                note=f'Assignment note {i+1}' if random.choice([True, False]) else '',
                ordering=random.choice(experiment_orders + [None]),
                group_index=random.randint(0, 5),
                alt_id=f'alt_{uuid.uuid4().hex[:8]}' if random.choice([True, False]) else ''
            )
            assignments.append(assignment)
        
        # Create results
        results = []
        for assignment in assignments:
            # Create 1-5 results per assignment
            battery_exps = list(assignment.battery.batteryexperiments_set.all())
            num_results = min(random.randint(1, 5), len(battery_exps))
            
            for j in range(num_results):
                result = Result.objects.create(
                    assignment=assignment,
                    battery_experiment=random.choice(battery_exps),
                    subject=assignment.subject,
                    status=random.choice(['not-started', 'started', 'completed', 'failed']),
                    include=random.choice(['not-set', 'n/a', 'include', 'reject']),
                    data=f'{{"trial_data": [{{"rt": {random.randint(200, 2000)}, "response": "{random.choice(["left", "right"])}"}}]}}'
                )
                results.append(result)

        self.stdout.write(
            f'Created {len(repo_origins)} repo origins, {len(experiment_repos)} experiments, '
            f'{len(experiment_instances)} instances, {len(subjects)} subjects, '
            f'{len(batteries)} batteries, {len(assignments)} assignments, {len(results)} results'
        )

    def create_prolific_data(self, count):
        """Create prolific-related data"""
        self.stdout.write('Creating prolific data...')
        
        batteries = list(Battery.objects.all())
        subjects = list(Subject.objects.filter(prolific_id__isnull=False))
        
        if not batteries:
            self.stdout.write(self.style.WARNING('No batteries found, skipping prolific data'))
            return
        
        # Create study collections
        study_collections = []
        for i in range(count):
            collection = StudyCollection.objects.create(
                name=f'Study Collection {i+1}',
                project=f'proj_{uuid.uuid4().hex[:8]}',
                workspace_id=f'ws_{uuid.uuid4().hex[:8]}',
                title=f'Research Study {i+1}: {random.choice(["Cognitive Assessment", "Memory Research", "Attention Study"])}',
                description=f'This is a research study investigating {random.choice(["cognitive processes", "memory formation", "attention mechanisms", "decision making"])}.',
                total_available_places=random.randint(50, 200),
                estimated_completion_time=random.randint(15, 90),
                reward=random.randint(200, 1500),  # In cents
                published=random.choice([True, False]),
                active=random.choice([True, False]),
                number_of_groups=random.randint(0, 4),
                inter_study_delay=timedelta(hours=random.randint(1, 48)) if random.choice([True, False]) else None,
                time_to_start_first_study=timedelta(hours=random.randint(1, 24)) if random.choice([True, False]) else None,
                failure_to_start_grace_interval=timedelta(hours=random.randint(1, 12)),
                failure_to_start_message='Please start the study within the specified time.',
                failure_to_start_warning_message='Warning: You have limited time to start this study.',
                study_time_to_warning=timedelta(hours=random.randint(12, 72)) if random.choice([True, False]) else None,
                study_warning_message='Please continue to the next part of the study.',
                study_grace_interval=timedelta(hours=random.randint(6, 24)) if random.choice([True, False]) else None,
                study_kick_on_timeout=random.choice([True, False]),
                collection_time_to_warning=timedelta(days=random.randint(3, 14)) if random.choice([True, False]) else None,
                collection_warning_message='Please complete all parts of the study collection.',
                collection_grace_interval=timedelta(days=random.randint(1, 7)) if random.choice([True, False]) else None,
                collection_kick_on_timeout=random.choice([True, False]),
                screener_rejection_message='Thank you for your interest. You do not qualify for this study.'
            )
            study_collections.append(collection)
        
        # Create parent-child relationships for some collections
        for i in range(len(study_collections)//3):
            child = study_collections[i]
            parent = random.choice(study_collections[len(study_collections)//2:])
            child.parent = parent
            child.save()
        
        # Create screener relationships
        for i in range(len(study_collections)//4):
            screener = study_collections[i]
            main_study = random.choice(study_collections[len(study_collections)//2:])
            screener.screener_for = main_study
            screener.save()
        
        # Create studies
        studies = []
        for collection in study_collections:
            # Create 2-5 studies per collection
            num_studies = random.randint(2, 5)
            collection_batteries = random.sample(batteries, min(num_studies, len(batteries)))
            
            for rank, battery in enumerate(collection_batteries):
                study = Study.objects.create(
                    battery=battery,
                    study_collection=collection,
                    rank=rank,
                    remote_id=f'prolific_{uuid.uuid4().hex[:8]}' if random.choice([True, False]) else '',
                    participant_group=f'pg_{uuid.uuid4().hex[:8]}' if random.choice([True, False]) else '',
                    completion_code=f'cc_{uuid.uuid4().hex[:8]}'
                )
                studies.append(study)
        
        # Create study ranks (additional ranking system)
        for study in studies[:count]:
            StudyRank.objects.create(
                study=study,
                rank=random.randint(1, 10)
            )
        
        # Create blocked participants
        blocked_participants = []
        prolific_ids = [f'blocked_{uuid.uuid4().hex[:8]}' for _ in range(count//2)]
        for prolific_id in prolific_ids:
            blocked = BlockedParticipant.objects.create(
                prolific_id=prolific_id,
                active=random.choice([True, False]),
                note=f'Blocked for {random.choice(["low quality responses", "failed attention checks", "incomplete submission", "duplicate participation"])}'
            )
            blocked_participants.append(blocked)
        
        # Create study collection subjects
        study_collection_subjects = []
        for collection in study_collections:
            # Add some subjects to each collection
            collection_subjects = random.sample(subjects, min(random.randint(5, 15), len(subjects)))
            
            for subject in collection_subjects:
                scs = StudyCollectionSubject.objects.create(
                    study_collection=collection,
                    subject=subject,
                    status=random.choice(['not-started', 'started', 'completed', 'failed', 'kicked']),
                    group_index=random.randint(0, collection.number_of_groups) if collection.number_of_groups > 0 else 0,
                    current_study=random.choice(list(collection.study_set.all())) if collection.study_set.exists() else None,
                    status_reason=random.choice(['n/a', 'study-timer', 'initial-timer', 'collection-timer']),
                    active=random.choice([True, False])
                )
                
                # Set some timing fields
                if random.choice([True, False]):
                    scs.ttfs_warned_at = timezone.now() - timedelta(hours=random.randint(1, 48))
                if random.choice([True, False]):
                    scs.ttcc_warned_at = timezone.now() - timedelta(days=random.randint(1, 7))
                    
                scs.save()
                study_collection_subjects.append(scs)
        
        # Create study subjects
        study_subjects = []
        for study in studies:
            # Add some subjects to each study
            study_subjects_list = random.sample(subjects, min(random.randint(3, 10), len(subjects)))
            
            for subject in study_subjects_list:
                # Get or create assignment for this subject and battery
                try:
                    assignment = Assignment.objects.filter(
                        subject=subject,
                        battery=study.battery
                    ).first()
                    if not assignment:
                        assignment = Assignment.objects.create(
                            subject=subject,
                            battery=study.battery,
                            status='not-started',
                            alt_id=study.remote_id
                        )
                except Exception as e:
                    # If there are issues, create a new assignment with unique alt_id
                    assignment = Assignment.objects.create(
                        subject=subject,
                        battery=study.battery,
                        status='not-started',
                        alt_id=f'{study.remote_id}_{uuid.uuid4().hex[:4]}'
                    )
                
                study_subject = StudySubject.objects.create(
                    study=study,
                    subject=subject,
                    assignment=assignment,
                    status=random.choice(['not-started', 'started', 'completed', 'failed', 'kicked']),
                    status_reason=random.choice(['n/a', 'study-timer', 'initial-timer']),
                    prolific_session_id=f'session_{uuid.uuid4().hex[:8]}' if random.choice([True, False]) else '',
                    added_to_study=timezone.now() - timedelta(days=random.randint(0, 30)) if random.choice([True, False]) else None
                )
                
                # Set timing fields
                if random.choice([True, False]):
                    study_subject.warned_at = timezone.now() - timedelta(hours=random.randint(1, 72))
                
                study_subject.save()
                study_subjects.append(study_subject)
        
        # Create simple completion codes
        simple_ccs = []
        for battery in random.sample(batteries, count//2):
            simple_cc = SimpleCC.objects.create(
                battery=battery,
                completion_url=f'https://app.prolific.co/submissions/complete?cc={uuid.uuid4().hex[:8]}'
            )
            simple_ccs.append(simple_cc)
        
        # Create prolific API results
        api_results = []
        for i in range(count):
            api_result = ProlificAPIResult.objects.create(
                request=f'POST /api/v1/studies/ - Study creation request {i+1}',
                response={
                    'status': random.choice(['success', 'error', 'pending']),
                    'id': f'study_{uuid.uuid4().hex[:8]}',
                    'message': random.choice(['Study created successfully', 'Participant added', 'Study published', 'Error occurred']),
                    'data': {'participants': random.randint(0, 50)}
                },
                collection=random.choice(study_collections) if random.choice([True, False]) else None
            )
            api_results.append(api_result)

        self.stdout.write(
            f'Created {len(study_collections)} study collections, {len(studies)} studies, '
            f'{len(study_collection_subjects)} collection subjects, {len(study_subjects)} study subjects, '
            f'{len(simple_ccs)} completion codes, {len(api_results)} API results'
        )

    def print_summary(self):
        """Print a summary of created data"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('DATA POPULATION SUMMARY'))
        self.stdout.write('='*50)
        
        # Users
        self.stdout.write(f'Users: {User.objects.count()}')
        self.stdout.write(f'Groups: {Group.objects.count()}')
        
        # Experiments
        self.stdout.write(f'Frameworks: {Framework.objects.count()}')
        self.stdout.write(f'Framework Resources: {FrameworkResource.objects.count()}')
        self.stdout.write(f'Repository Origins: {RepoOrigin.objects.count()}')
        self.stdout.write(f'Experiment Repositories: {ExperimentRepo.objects.count()}')
        self.stdout.write(f'Experiment Instances: {ExperimentInstance.objects.count()}')
        self.stdout.write(f'Batteries: {Battery.objects.count()}')
        self.stdout.write(f'Battery Experiments: {BatteryExperiments.objects.count()}')
        self.stdout.write(f'Subjects: {Subject.objects.count()}')
        self.stdout.write(f'Assignments: {Assignment.objects.count()}')
        self.stdout.write(f'Results: {Result.objects.count()}')
        self.stdout.write(f'Experiment Orders: {ExperimentOrder.objects.count()}')
        self.stdout.write(f'Order Items: {ExperimentOrderItem.objects.count()}')
        
        # Prolific
        self.stdout.write(f'Study Collections: {StudyCollection.objects.count()}')
        self.stdout.write(f'Studies: {Study.objects.count()}')
        self.stdout.write(f'Study Ranks: {StudyRank.objects.count()}')
        self.stdout.write(f'Study Subjects: {StudySubject.objects.count()}')
        self.stdout.write(f'Study Collection Subjects: {StudyCollectionSubject.objects.count()}')
        self.stdout.write(f'Simple Completion Codes: {SimpleCC.objects.count()}')
        self.stdout.write(f'Prolific API Results: {ProlificAPIResult.objects.count()}')
        self.stdout.write(f'Blocked Participants: {BlockedParticipant.objects.count()}')
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('Test data population completed successfully!')
        self.stdout.write('You can now log in with:')
        self.stdout.write('  Username: admin')
        self.stdout.write('  Password: admin123')
        self.stdout.write('='*50)
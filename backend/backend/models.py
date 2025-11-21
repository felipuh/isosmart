from django.db import models
from django.contrib.postgres.fields import JSONField

class ContextAnalysis(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    internal_insights = models.JSONField()
    external_insights = models.JSONField()
    status = models.CharField(max_length=20)
    
    class Meta:
        db_table = 'context_analysis'
        ordering = ['-timestamp']

class StakeholderProfile(models.Model):
    name = models.CharField(max_length=200)
    stakeholder_type = models.CharField(max_length=50)
    influence_score = models.FloatField()
    expectations = models.JSONField()
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stakeholder_profiles'

class ProcessMap(models.Model):
    process_id = models.CharField(max_length=50, unique=True)
    process_name = models.CharField(max_length=200)
    process_data = models.JSONField()
    diagram_url = models.URLField(blank=True)
    predicted_risks = models.JSONField()
    generated_kpis = models.JSONField()
    
    class Meta:
        db_table = 'process_maps'

class RiskMatrix(models.Model):
    source_module = models.CharField(max_length=10)  # SCA, SIE, SPM
    risk_description = models.TextField()
    probability = models.CharField(max_length=20)
    impact = models.CharField(max_length=20)
    mitigation_actions = models.TextField()
    iso_clause = models.CharField(max_length=10)
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'risk_matrix'
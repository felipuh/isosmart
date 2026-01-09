from rest_framework import serializers
from .models import Document
from django.core.validators import FileExtensionValidator
import os

class DocumentSerializer(serializers.ModelSerializer):
    file_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'content',
            'document_type',
            'source',
            'file_path',
            'file_name',
            'file_url',
            'uploaded_by',
            'created_at',
            'updated_at',
            'is_processed',
            'processed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'file_path']
    
    def get_file_name(self, obj):
        """Obtener solo el nombre del archivo"""
        if obj.file_path:
            return os.path.basename(str(obj.file_path.name))
        return None
    
    def get_file_url(self, obj):
        """Obtener URL del archivo"""
        if obj.file_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file_path.url)
            return obj.file_path.url
        return None


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer para upload de documentos"""
    title = serializers.CharField(max_length=255)
    content = serializers.CharField(required=False, allow_blank=True)
    document_type = serializers.ChoiceField(
        choices=Document.TYPE_CHOICES
    )
    file = serializers.FileField(
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'docx', 'doc', 'txt', 'xlsx', 'xls']
        )]
    )
    source = serializers.CharField(max_length=255, required=False)
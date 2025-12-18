from rest_framework import serializers
from .models import Document
from django.core.validators import FileExtensionValidator
import os

class DocumentSerializer(serializers.ModelSerializer):
    file_size_mb = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'description',
            'document_type',
            'file_path',
            'file_name',
            'file_size',
            'file_size_mb',
            'uploaded_by',
            'uploaded_at',
            'is_active',
            'metadata'
        ]
        read_only_fields = ['id', 'uploaded_at', 'file_size']
    
    def get_file_size_mb(self, obj):
        """Convertir tamaño a MB"""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0
    
    def get_file_name(self, obj):
        """Obtener solo el nombre del archivo"""
        if obj.file_path:
            return os.path.basename(str(obj.file_path))
        return None
    
    def validate_file_path(self, value):
        """Validar extensión de archivo"""
        allowed_extensions = ['pdf', 'docx', 'doc', 'txt', 'xlsx', 'xls']
        ext = value.name.split('.')[-1].lower()
        
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(allowed_extensions)}"
            )
        
        # Validar tamaño máximo (10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                "El archivo es demasiado grande. Tamaño máximo: 10MB"
            )
        
        return value


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer para upload de documentos"""
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    document_type = serializers.ChoiceField(
        choices=[
            ('policy', 'Política'),
            ('procedure', 'Procedimiento'),
            ('manual', 'Manual'),
            ('report', 'Reporte'),
            ('plan', 'Plan'),
            ('other', 'Otro')
        ]
    )
    file = serializers.FileField(
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'docx', 'doc', 'txt', 'xlsx', 'xls']
        )]
    )
    uploaded_by = serializers.CharField(max_length=100, required=False)
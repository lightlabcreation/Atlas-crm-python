from django import forms
from .models import StockKeeperTask

class StockKeeperTaskForm(forms.ModelForm):
    class Meta:
        model = StockKeeperTask
        fields = ['title', 'description', 'task_type', 'priority', 'due_date', 'estimated_duration']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Enter task title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': 'Enter task description'
            }),
            'task_type': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'type': 'datetime-local'
            }),
            'estimated_duration': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Duration in minutes'
            })
        } 
CRITIC_VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "approved": {
            "type": "boolean",
            "description": "Şarkı sözü hece ölçüsü, kafiye ve akıcılık açısından yeterliyse true",
        },
        "issues": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Tespit edilen sorunların kısa listesi (boş olabilir)",
        },
        "feedback": {
            "type": "string",
            "description": "Söz yazarına iletilecek somut, uygulanabilir revizyon geri bildirimi",
        },
    },
    "required": ["approved", "issues", "feedback"],
}

TRACKLIST_SCHEMA = {
    "type": "object",
    "properties": {
        "album_title": {"type": "string"},
        "tracks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "mood": {
                        "type": "string",
                        "description": "Parçanın duygu durumu/atmosferi (örn. 'öfkeli ve hızlı', 'melankolik ve yavaş')",
                    },
                },
                "required": ["title", "mood"],
            },
        },
    },
    "required": ["album_title", "tracks"],
}

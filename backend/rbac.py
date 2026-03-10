class RBAC:
    ROLES = {
        "Scientist": ["view_all", "view_classified", "edit_docs"],
        "Engineer": ["view_all", "view_technical"],
        "Analyst": ["view_mission_stats"],
        "Public": ["view_public"]
    }

    # Document access levels mapping
    DOC_ACCESS = {
        "classified": ["Scientist"],
        "technical": ["Scientist", "Engineer"],
        "mission_stats": ["Scientist", "Engineer", "Analyst"],
        "public": ["Scientist", "Engineer", "Analyst", "Public"]
    }

    @staticmethod
    def get_role_permissions(role):
        return RBAC.ROLES.get(role, [])

    @staticmethod
    def check_access(user_role, doc_type):
        """
        Checks if a user has access to a specific document type.
        """
        allowed_roles = RBAC.DOC_ACCESS.get(doc_type, [])
        return user_role in allowed_roles

    @staticmethod
    def filter_documents(user_role, documents):
        """
        Filters out documents that the user is not allowed to see based on metadata.
        Assumes documents have 'access_level' metadata.
        """
        if not documents:
            return []
            
        filtered_docs = []
        for doc in documents:
            doc_level = doc.metadata.get("access_level", "public") # Default to public
            if RBAC.check_access(user_role, doc_level):
                filtered_docs.append(doc)
        
        return filtered_docs

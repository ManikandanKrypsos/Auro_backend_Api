// ─────────────────────────────────────────────────────────────────────────────
//  DATA MODEL
// ─────────────────────────────────────────────────────────────────────────────

enum UserRole { admin, receptionist, therapist }

enum UserStatus { active, inactive }

class StaffUser {
  final String id;
  final String username;
  final String email;
  final String phone;
  final UserRole role;
  UserStatus status;

  StaffUser({
    required this.id,
    required this.username,
    required this.email,
    required this.phone,
    required this.role,
    this.status = UserStatus.active,
  });

  String get roleLabel {
    switch (role) {
      case UserRole.admin:        return 'Admin';
      case UserRole.receptionist: return 'Receptionist';
      case UserRole.therapist:    return 'Therapist';
    }
  }
}
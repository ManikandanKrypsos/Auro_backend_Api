enum StaffRole { therapist, receptionist }

enum StaffStatus { active, onLeave, inactive }

class StaffModel {
  final String name;
  final String role;
  final String rating;
  final String experience;
  final StaffStatus status;
  final StaffRole jobRole;
  final String image;

  const StaffModel({
    required this.name,
    required this.role,
    required this.rating,
    required this.experience,
    required this.status,
    required this.jobRole,
    required this.image,
  });

  String get statusLabel {
    switch (status) {
      case StaffStatus.active:
        return 'ACTIVE';
      case StaffStatus.onLeave:
        return 'ON LEAVE';
      case StaffStatus.inactive:
        return 'INACTIVE';
    }
  }
}
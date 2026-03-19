class PatientModel {
  final String name;
  final String id;
  final String phone;
  final String image;

  final bool isNew;

  const PatientModel({
    required this.name,
    required this.id,
    required this.phone,
    required this.image,
    this.isNew = false,
  });
}
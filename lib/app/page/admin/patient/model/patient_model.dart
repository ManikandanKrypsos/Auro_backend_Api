import 'package:cloud_firestore/cloud_firestore.dart';

class PatientModel {
  final String id;
  final String name;
  final String email;
  final String phone;
  final String city;
  final String country;
  final String gender;
  final String dob;
  final String bloodType;
  final String allergies;
  final String skinType;
  final String contraindications;
  final String marketingSource;
  final String image;
  final String category;
  final DateTime? createdAt;

  const PatientModel({
    required this.id,
    required this.name,
    this.email = '',
    required this.phone,
    this.city = '',
    this.country = '',
    this.gender = '',
    this.dob = '',
    this.bloodType = '',
    this.allergies = '',
    this.skinType = '',
    this.contraindications = '',
    this.marketingSource = '',
    required this.image,
    this.category = 'New',
    this.createdAt,
  });

  factory PatientModel.fromJson(Map<String, dynamic> json, String documentId) {
    return PatientModel(
      id: documentId,
      name: json['name'] ?? '',
      email: json['email'] ?? '',
      phone: json['phone'] ?? '',
      city: json['city'] ?? '',
      country: json['country'] ?? '',
      gender: json['gender'] ?? '',
      dob: json['dob'] ?? '',
      bloodType: json['bloodType'] ?? '',
      allergies: json['allergies'] ?? '',
      skinType: json['skinType'] ?? '',
      contraindications: json['contraindications'] ?? '',
      marketingSource: json['marketingSource'] ?? '',
      image: json['image'] ?? '',
      category: json['category'] ?? 'New',
      createdAt: json['createdAt'] != null
          ? (json['createdAt'] as Timestamp).toDate()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'email': email,
      'phone': phone,
      'city': city,
      'country': country,
      'gender': gender,
      'dob': dob,
      'bloodType': bloodType,
      'allergies': allergies,
      'skinType': skinType,
      'contraindications': contraindications,
      'marketingSource': marketingSource,
      'image': image,
      'category': category,
      'createdAt': createdAt != null
          ? Timestamp.fromDate(createdAt!)
          : FieldValue.serverTimestamp(),
    };
  }
}
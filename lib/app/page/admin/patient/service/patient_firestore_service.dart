import 'package:cloud_firestore/cloud_firestore.dart';
import '../model/patient_model.dart';

class PatientFirestoreService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;
  final String collectionPath = 'patients';

  Future<void> addPatient(PatientModel patient) async {
    try {
      await _db.collection(collectionPath).add(patient.toJson());
    } catch (e) {
      throw Exception('Failed to add patient: $e');
    }
  }

  Future<void> updatePatient(PatientModel patient) async {
    try {
      await _db.collection(collectionPath).doc(patient.id).update(patient.toJson());
    } catch (e) {
      throw Exception('Failed to update patient: $e');
    }
  }

  Stream<List<PatientModel>> getPatientsStream() {
    return _db
        .collection(collectionPath)
        .orderBy('createdAt', descending: true)
        .snapshots()
        .map((snapshot) => snapshot.docs
            .map((doc) => PatientModel.fromJson(doc.data(), doc.id))
            .toList());
  }

  Future<List<PatientModel>> getPatientsFuture() async {
    try {
      final snapshot = await _db.collection(collectionPath).get();
      return snapshot.docs
          .map((doc) => PatientModel.fromJson(doc.data(), doc.id))
          .toList();
    } catch (e) {
      throw Exception('Failed to fetch patients: $e');
    }
  }
}

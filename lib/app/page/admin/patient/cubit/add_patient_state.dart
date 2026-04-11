part of 'add_patient_cubit.dart';

enum AddPatientStatus { initial, loading, success, error }

class AddPatientState {
  final String gender;
  final String marketingSource;
  final String skinType;
  final AddPatientStatus status;
  final String errorMessage;

  const AddPatientState({
    this.gender = 'Female',
    this.marketingSource = '',
    this.skinType = '',
    this.status = AddPatientStatus.initial,
    this.errorMessage = '',
  });

  AddPatientState copyWith({
    String? gender,
    String? marketingSource,
    String? skinType,
    AddPatientStatus? status,
    String? errorMessage,
  }) {
    return AddPatientState(
      gender: gender ?? this.gender,
      marketingSource: marketingSource ?? this.marketingSource,
      skinType: skinType ?? this.skinType,
      status: status ?? this.status,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }
}

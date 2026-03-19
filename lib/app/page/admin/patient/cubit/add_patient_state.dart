part of 'add_patient_cubit.dart';


class AddPatientState {
  final String gender;
  final String marketingSource;
  final String skinType;

  const AddPatientState({
    this.gender = 'Female',
    this.marketingSource = '',
    this.skinType = '',
  });

  AddPatientState copyWith({
    String? gender,
    String? marketingSource,
    String? skinType,
  }) {
    return AddPatientState(
      gender: gender ?? this.gender,
      marketingSource: marketingSource ?? this.marketingSource,
      skinType: skinType ?? this.skinType,
    );
  }
}

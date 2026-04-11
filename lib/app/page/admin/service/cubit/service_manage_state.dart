part of 'service_manage_cubit.dart';

class ServiceManageState {
  final int categoryTab;
  final List<String> contraindications;
  final String freqUnit;
  final String roomType;
  final List<String> equipmentTags;
  final List<String> consumableTags;
  final List<String> assignedStaff;
 
  const ServiceManageState({
    this.categoryTab = 0,
    this.contraindications = const [],
    this.freqUnit = 'Weeks',
    this.roomType = 'Therapy Suite A',
    this.equipmentTags = const [],
    this.consumableTags = const [],
    this.assignedStaff = const [],
  });
 
  ServiceManageState copyWith({
    int? categoryTab,
    List<String>? contraindications,
    String? freqUnit,
    String? roomType,
    List<String>? equipmentTags,
    List<String>? consumableTags,
    List<String>? assignedStaff,
  }) {
    return ServiceManageState(
      categoryTab: categoryTab ?? this.categoryTab,
      contraindications: contraindications ?? this.contraindications,
      freqUnit: freqUnit ?? this.freqUnit,
      roomType: roomType ?? this.roomType,
      equipmentTags: equipmentTags ?? this.equipmentTags,
      consumableTags: consumableTags ?? this.consumableTags,
      assignedStaff: assignedStaff ?? this.assignedStaff,
    );
  }
}

